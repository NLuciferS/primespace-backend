# PrimeSpace Demo Backend (SQLite)

This backend is **demo-focused**: stable, simple setup, real password auth + stored bookings.

## Features

- Email/password registration + login (JWT)
- Roles: `customer`, `provider`, `admin`
- Venues API (seeded)
- Bookings stored in SQLite
- CORS for local static frontend (port 5500)

## Setup (Windows / PowerShell)

From this folder:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set `SECRET_KEY` to any long random string.

## Run

```powershell
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Test in browser:
- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

## Frontend

Serve your static frontend:

```powershell
cd D:\Games\PrimeSpace\primespace
python -m http.server 5500
```

Open:
- `http://127.0.0.1:5500/customer-register.html`
- `http://127.0.0.1:5500/login.html`

## API Quick Notes

- `POST /auth/register` JSON body: `{ "name", "email", "password", "role" }`
- `POST /auth/login` supports:
  - JSON body: `{ "email", "password" }`
  - form body: `username` + `password` (compat with existing frontend)
- `POST /bookings` requires `Authorization: Bearer <token>` and **customer role**

