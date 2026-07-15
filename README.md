# Trekking Management Application

A Flask-based web application for managing treks, trek staff and trekkers.
It supports three roles — **Admin**, **Trek Staff**, and **Trekker (User)** —
each with a dedicated dashboard, and covers the full booking lifecycle: trek
creation, staff assignment, trek discovery, slot-aware booking, and status
tracking through Open, Closed, Started, Ongoing and Completed states.

Built as part of the Modern Application Development I (App Dev I) course project.

## Tech Stack

- **Flask** — backend web framework
- **Flask-SQLAlchemy** — ORM over a SQLite database
- **Jinja2** — server-side templating
- **Bootstrap 5** (via CDN) — frontend styling

## Project Structure

```
project_root/
├── app.py                     # Application entry point; creates tables + admin user
├── init_db.py                 # One-time script to reset the DB schema (dev only)
├── requirements.txt
├── .gitignore
├── application/
│   ├── __init__.py
│   ├── database.py            # Shared SQLAlchemy db instance
│   ├── models.py               # User, StaffProfile, Trek, Booking models
│   └── controllers.py          # All routes (Blueprint), grouped by role
└── templates/
    ├── base.html               # Common layout with role-aware navbar
    ├── login.html, register.html
    ├── admin_*.html             # Admin screens
    ├── staff_*.html             # Trek Staff screens
    ├── trekker_*.html           # Trekker screens
    └── errors/
        └── 404.html
```

## Setup & Running the App

1. **Clone the repository and move into the project folder.**

2. **Create and activate a virtual environment (recommended).**
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

3. **Install dependencies.**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application.**
   ```bash
   python app.py
   ```
   On first run, `app.py` automatically creates `trekking.db` (SQLite) with all
   tables and pre-creates the Admin account — no manual DB setup needed.

5. **Open the app** at `http://127.0.0.1:5000/` in your browser.

### Default Admin Login
```
Username: admin
Password: admin123
```

### Resetting the Database
If the models change and you need to rebuild the schema from scratch
(`db.create_all()` does not alter existing tables), run:
```bash
python init_db.py
```
⚠️ This drops and recreates all tables — all existing data will be lost.

## Roles & Features

**Admin**
- Dashboard with trek/user/staff/booking counts and recent bookings
- Full trek CRUD, with staff assignment
- Approve / blacklist trek staff requests
- Search, block/unblock and remove trekker accounts
- View all system booking records

**Trek Staff**
- Register (requires Admin approval before login) and update profile
- View assigned treks with participant counts
- Update trek status and available slots
- Manage / remove participants for their treks

**Trekker (User)**
- Register and log in directly, update profile
- Search and filter open treks by location and difficulty
- Book a trek (with duplicate-booking and full/closed-trek checks)
- Cancel a booking, and view completed trek history

## Notes

- Passwords and session-based auth are implemented at a basic level for
  coursework purposes; the app uses Flask sessions (not Flask-Login) with a
  `before_request` guard restricting `/admin`, `/staff` and `/trekker` routes
  by role.
- The AI/LLM usage declaration and demo video link are included in the
  project report (`App_Dev_Project_Report.docx` / PDF).