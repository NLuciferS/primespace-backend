import os
import traceback
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import models
import schemas
from db import engine, Base, get_db, SessionLocal
import security
from seed import ensure_seed_data

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PrimeSpace Demo API", version="1.0.0")


def _origins():
    raw = (os.getenv("FRONTEND_ORIGINS") or "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return ["http://127.0.0.1:5500", "http://localhost:5500", "null"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    # For demo stability: never drop the connection, always return JSON.
    # Keep detail generic; real detail stays in server console traceback.
    print("Unhandled exception:", repr(exc))
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
def _seed():
    db = SessionLocal()
    try:
        ensure_seed_data(db)
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    payload = security.decode_token(token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token payload.")
    user = db.query(models.User).filter(models.User.id == int(sub)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists.")
    return user


def require_role(*roles: str):
    def checker(user: models.User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Access denied.")
        return user

    return checker


@app.get("/")
def root():
    return {"message": "PrimeSpace Demo API is running!"}


@app.post("/auth/register", response_model=schemas.UserOut, responses={422: {"model": schemas.ErrorOut}})
def register(request: Request, user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    email = user_in.email.lower()
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    hashed = security.hash_password(user_in.password)
    user = models.User(name=user_in.name, email=email, hashed_password=hashed, role=models.UserRole(user_in.role.value))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.TokenOut, responses={401: {"model": schemas.ErrorOut}, 422: {"model": schemas.ErrorOut}})
async def login(request: Request, db: Session = Depends(get_db)):
    # Compatibility mode:
    # - JSON: { "email": "...", "password": "..." }
    # - Form: email/password from frontend using OAuth2 style { username, password }
    ctype = (request.headers.get("content-type") or "").lower()
    email: Optional[str] = None
    password: Optional[str] = None

    if "application/json" in ctype:
        body = await request.json()
        email = (body.get("email") or "").strip()
        password = (body.get("password") or "").strip()
    else:
        form = await request.form()
        # OAuth2PasswordRequestForm sends "username"
        email = (form.get("email") or form.get("username") or "").strip()
        password = (form.get("password") or "").strip()

    if not email or not password:
        raise HTTPException(status_code=422, detail="Email and password are required.")

    user = db.query(models.User).filter(models.User.email == email.lower()).first()
    if not user or not security.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")

    token = security.create_access_token(user_id=user.id, role=user.role.value)
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.get("/auth/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user


@app.patch("/auth/me", response_model=schemas.UserOut)
def update_me(update: schemas.UserUpdate, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if update.name is not None:
        user.name = update.name.strip()
    db.commit()
    db.refresh(user)
    # Update localStorage-compatible response
    return user


@app.get("/venues", response_model=list[schemas.VenueOut])
def list_venues(db: Session = Depends(get_db)):
    venues = db.query(models.Venue).all()
    # Convert rating int*10 -> float for frontend
    out: list[schemas.VenueOut] = []
    for v in venues:
        out.append(
            schemas.VenueOut(
                id=v.id,
                name=v.name,
                location=v.location,
                city=v.city,
                venue_type=v.venue_type,
                capacity=v.capacity,
                rating=(v.rating or 0) / 10.0,
                price=v.price,
            )
        )
    return out


@app.get("/venues/{venue_id}", response_model=schemas.VenueOut)
def get_venue(venue_id: str, db: Session = Depends(get_db)):
    v = db.query(models.Venue).filter(models.Venue.id == venue_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Venue not found.")
    return schemas.VenueOut(
        id=v.id,
        name=v.name,
        location=v.location,
        city=v.city,
        venue_type=v.venue_type,
        capacity=v.capacity,
        rating=(v.rating or 0) / 10.0,
        price=v.price,
    )


@app.post("/bookings", response_model=schemas.BookingOut)
def create_booking(
    booking_in: schemas.BookingCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("customer")),
):
    v = db.query(models.Venue).filter(models.Venue.id == booking_in.venue_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Venue not found.")
    if booking_in.guests > v.capacity:
        raise HTTPException(status_code=422, detail=f"Guests cannot exceed venue capacity ({v.capacity}).")

    # Check for double booking on same date
    existing = db.query(models.Booking).filter(
        models.Booking.venue_id == booking_in.venue_id,
        models.Booking.date == booking_in.date
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="This venue is already booked on that date.")

    # Calculate price server side — never trust the client
    multiplier = 1.12 if booking_in.guests > v.capacity * 0.75 else 1.0
    server_total = round((v.price * multiplier) * 1.1)  # includes 10% service fee

    booking = models.Booking(
        user_id=user.id,
        venue_id=booking_in.venue_id,
        date=booking_in.date,
        guests=booking_in.guests,
        total=server_total,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@app.get("/bookings/me", response_model=list[schemas.BookingOut])
def my_bookings(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    bookings = db.query(models.Booking).filter(models.Booking.user_id == user.id).order_by(models.Booking.id.desc()).all()
    return bookings


@app.get("/bookings/all", response_model=list[schemas.BookingOut])
def all_bookings(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    # Providers and admins can see all bookings
    if user.role.value not in ["provider", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    bookings = db.query(models.Booking).order_by(models.Booking.id.desc()).all()
    return bookings


@app.get("/venues/{venue_id}/availability")
def get_availability(venue_id: str, db: Session = Depends(get_db)):
    v = db.query(models.Venue).filter(models.Venue.id == venue_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Venue not found.")

    all_dates = [d.strip() for d in v.availability_dates.split(",") if d.strip()]

    # Get confirmed booked dates
    booked = db.query(models.Booking).filter(
        models.Booking.venue_id == venue_id,
        models.Booking.status == models.BookingStatus.confirmed
    ).all()
    booked_dates = set()
    for b in booked:
        if b.date and "-" in b.date:
            parts = b.date.split("-")
            if len(parts) == 3:
                booked_dates.add(f"{parts[2]}/{parts[1]}/{parts[0]}")
        else:
            booked_dates.add(b.date)

    available = [d for d in all_dates if d not in booked_dates]
    return {"venue_id": venue_id, "available_dates": available}


@app.patch("/bookings/{booking_id}/cancel", response_model=schemas.BookingOut)
def cancel_booking(booking_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only cancel your own bookings.")
    if booking.status == models.BookingStatus.cancelled:
        raise HTTPException(status_code=400, detail="Booking is already cancelled.")
    booking.status = models.BookingStatus.cancelled
    db.commit()
    db.refresh(booking)
    return booking
