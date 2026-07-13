# Trekking Management Application

A Flask + SQLAlchemy web application for managing treks, trek staff, and
trekker bookings, built for the Modern Application Development I course
project (Milestones 0–4: schema setup, auth, admin dashboard, staff
dashboard, and user dashboard/booking system).

## Roles
- **Admin** (pre-created, no self-registration): manages treks, staff,
  users, and bookings.
- **Trek Staff** (registers, needs Admin approval): manages assigned
  treks and their participants.
- **Trekker / User** (registers): browses, books, and tracks treks.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

The app creates `trekking.db` automatically on first run and seeds a
default Admin account:

- Username: `admin`
- Password: `admin123`

If you've changed the models and need to rebuild the schema from
scratch (this wipes all data), run:

```bash
python init_db.py
```

## Project Structure

```
trekking-management/
├── app.py                 # App entry point, blueprint + db registration
├── init_db.py              # One-time schema reset script
├── requirements.txt
├── application/
│   ├── __init__.py
│   ├── database.py         # SQLAlchemy instance
│   ├── models.py           # User, StaffProfile, Trek, Booking models
│   └── controllers.py      # Routes / view logic
└── templates/               # Jinja2 templates (Bootstrap styled)
    ├── base.html
    ├── login.html
    ├── register.html
    ├── admin_*.html
    ├── staff_*.html
    ├── trekker_*.html
    └── errors/404.html
```
