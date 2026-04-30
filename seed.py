from sqlalchemy.orm import Session
import models


VENUE_DATA = [
    ("executive-conference-center", "Executive Conference Center", "123 Bishopsgate, City of London", "London", "Conference", 200, 48, 2500, "28/04/2026,05/05/2026,12/05/2026,19/05/2026"),
    ("skyline-meeting-hall", "Skyline Meeting Hall", "45 Deansgate, Manchester City Centre", "Manchester", "Meeting", 150, 46, 1800, "25/04/2026,02/05/2026,16/05/2026,23/05/2026"),
    ("innovation-hub", "Innovation Hub", "12 Temple Row, Birmingham City Centre", "Birmingham", "Workshop", 100, 49, 1500, "30/04/2026,07/05/2026,21/05/2026,04/06/2026"),
    ("grand-conference-suite", "Grand Conference Suite", "8 Royal Terrace, Edinburgh New Town", "Edinburgh", "Conference", 500, 47, 5000, "01/05/2026,15/05/2026,29/05/2026,12/06/2026"),
    ("boardroom-premier", "Boardroom Premier", "3 Park Place, Cardiff City Centre", "Cardiff", "Boardroom", 30, 45, 800, "24/04/2026,08/05/2026,22/05/2026,05/06/2026"),
    ("waterfront-event-space", "Waterfront Event Space", "1 Harbourside, Bristol Waterfront", "Bristol", "Conference", 250, 48, 3200, "29/04/2026,13/05/2026,27/05/2026,10/06/2026"),
    ("leeds-central-suite", "Leeds Central Suite", "10 Wellington Street, Leeds City Centre", "Leeds", "Conference", 180, 46, 2200, "26/04/2026,03/05/2026,17/05/2026,31/05/2026"),
    ("glasgow-summit-hall", "Glasgow Summit Hall", "32 Buchanan Street, Glasgow City Centre", "Glasgow", "Meeting", 120, 45, 1600, "27/04/2026,11/05/2026,18/05/2026,01/06/2026"),
    ("liverpool-dock-venue", "Liverpool Dock Venue", "5 Albert Dock, Liverpool Waterfront", "Liverpool", "Conference", 350, 48, 4200, "30/04/2026,09/05/2026,23/05/2026,06/06/2026"),
    ("nottingham-business-hub", "Nottingham Business Hub", "14 Maid Marian Way, Nottingham City Centre", "Nottingham", "Workshop", 80, 44, 1100, "28/04/2026,12/05/2026,26/05/2026,09/06/2026"),
    ("newcastle-corporate-centre", "Newcastle Corporate Centre", "6 Grey Street, Newcastle City Centre", "Newcastle", "Conference", 160, 45, 1900, "25/04/2026,06/05/2026,20/05/2026,03/06/2026"),
    ("sheffield-meeting-rooms", "Sheffield Meeting Rooms", "22 Division Street, Sheffield City Centre", "Sheffield", "Boardroom", 50, 43, 950, "24/04/2026,10/05/2026,24/05/2026,07/06/2026"),
]


def ensure_seed_data(db: Session):
    if db.query(models.Venue).count() > 0:
        return
    venues = [
        models.Venue(
            id=vid, name=name, location=loc, city=city,
            venue_type=vtype, capacity=cap, rating=rating,
            price=price, availability_dates=dates
        )
        for vid, name, loc, city, vtype, cap, rating, price, dates in VENUE_DATA
    ]
    db.add_all(venues)
    db.commit()
