"""
One-time schema reset script for Milestone 1.

Why this is needed:
SQLAlchemy's db.create_all() (used in app.py) only creates tables that
don't already exist -- it will NOT add new columns to a table that's
already there. Since we added new columns (Trek.start_date, Trek.end_date,
Trek.description, User.contact_details, Booking.completed_on), the old
trekking.db file needs to be rebuilt from the updated models.

This is done entirely through code (SQLAlchemy ORM), not through any
manual DB tool, so it stays compliant with the "no manual DB creation"
guideline.

Usage:
    python reset_db.py

This will WIPE all existing data and recreate empty tables + the admin
user. Only run this in development, before you have real submission data
you want to keep.
"""

from app import app
from application.database import db
from application.models import User


with app.app_context():
    db.drop_all()
    db.create_all()

    admin = User.query.filter_by(username='admin').first()
    if admin is None:
        admin_user = User(username='admin', password='admin123', role='Admin')
        db.session.add(admin_user)
        db.session.commit()

    print("Database reset complete. Tables recreated with updated schema.")
    print("Admin login -> username: admin / password: admin123")