from flask import Flask
from models import db, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    admin_user = User.query.filter_by(role='Admin').first()
    if not admin_user:
        admin = User(username='admin', password='adminpass24', role='Admin')
        db.session.add(admin)
        db.session.commit()