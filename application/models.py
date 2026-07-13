from application.database import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    contact_details = db.Column(db.String(200), nullable=True)

    # Relationships (Trek Staff <-> Trek, User <-> Booking)
    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False)
    treks = db.relationship('Trek', backref='assigned_staff', foreign_keys='Trek.assigned_staff_id')
    bookings = db.relationship('Booking', backref='user', lazy=True)


class StaffProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    name = db.Column(db.String(120), nullable=False)
    contact_details = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), nullable=False)


class Trek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trek_name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)

    # Relationship (Trek <-> Booking)
    bookings = db.relationship('Booking', backref='trek', lazy=True)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    completed_on = db.Column(db.DateTime, nullable=True)