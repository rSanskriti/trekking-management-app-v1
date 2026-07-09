from flask import Blueprint, render_template, request, redirect, url_for, session
from application.database import db
from application.models import User, StaffProfile

controllers = Blueprint('controllers', __name__)


@controllers.route('/')
def home():
    return 'Home'


@controllers.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        if not username or not password or role not in ['Trekker', 'Trek Staff']:
            return render_template('register.html', error='Invalid registration data')
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error='Username already exists')
        user = User(username=username, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        if role == 'Trek Staff':
            profile = StaffProfile(user_id=user.id, name=request.form.get('name', ''), contact_details=request.form.get('contact_details', ''), status='Pending')
            db.session.add(profile)
            db.session.commit()
        return redirect(url_for('controllers.login'))
    return render_template('register.html')


@controllers.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, password=password).first()
        if not user:
            return render_template('login.html', error='Invalid credentials')
        if user.role == 'Trek Staff':
            profile = StaffProfile.query.filter_by(user_id=user.id).first()
            if not profile or profile.status != 'Approved':
                return render_template('login.html', error='Staff account is not approved')
        session['user_id'] = user.id
        session['role'] = user.role
        if user.role == 'Admin':
            return redirect(url_for('controllers.admin_dashboard'))
        if user.role == 'Trek Staff':
            return redirect(url_for('controllers.staff_dashboard'))
        return redirect(url_for('controllers.trekker_dashboard'))
    return render_template('login.html')


@controllers.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('controllers.login'))


@controllers.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'Admin':
        return redirect(url_for('controllers.login'))
    return render_template('admin_dashboard.html')


@controllers.route('/staff/dashboard')
def staff_dashboard():
    if session.get('role') != 'Trek Staff':
        return redirect(url_for('controllers.login'))
    return render_template('staff_dashboard.html')


@controllers.route('/trekker/dashboard')
def trekker_dashboard():
    if session.get('role') != 'Trekker':
        return redirect(url_for('controllers.login'))
    return render_template('trekker_dashboard.html')