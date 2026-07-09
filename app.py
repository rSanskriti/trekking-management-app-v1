from flask import Flask
from application.database import db
from application.models import User
from application.controllers import controllers

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.register_blueprint(controllers)
db.init_app(app)

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    if admin is None:
        admin_user = User(username='admin', password='admin123', role='Admin')
        db.session.add(admin_user)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)