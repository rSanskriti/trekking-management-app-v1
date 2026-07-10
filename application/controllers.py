from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from sqlalchemy import or_
from datetime import datetime
from application.database import db
from application.models import User, StaffProfile, Trek, Booking

controllers = Blueprint('controllers', __name__)


def parse_date(value):
    """Convert an HTML <input type="date"> value ('YYYY-MM-DD') into a
    Python date object. Returns None if empty/invalid so bad input never
    crashes the request."""
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def get_approved_staff_list():
    """Shared helper: Approved Trek Staff users, formatted for the
    Assign Staff dropdown."""
    staff_profiles = StaffProfile.query.filter_by(status='Approved').all()
    staff_list = []
    for profile in staff_profiles:
        user = User.query.get(profile.user_id)
        if user and user.role == 'Trek Staff':
            staff_list.append({'id': user.id, 'name': profile.name})
    return staff_list


@controllers.route('/')
def home():
    return redirect(url_for('controllers.login'))


@controllers.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        name = request.form.get('name')
        contact_details = request.form.get('contact_details')

        if not username or not password or role not in ['Trekker', 'Trek Staff']:
            flash('Invalid registration data')
            return redirect(url_for('controllers.register'))
        if password != confirm_password:
            flash('Password and Confirm Password do not match')
            return redirect(url_for('controllers.register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('controllers.register'))

        user = User(username=username, password=password, role=role)
        db.session.add(user)
        db.session.commit()

        if role == 'Trek Staff':
            profile = StaffProfile(
                user_id=user.id,
                name=name or '',
                contact_details=contact_details or '',
                status='Pending'
            )
            db.session.add(profile)
            db.session.commit()

        flash('Registration successful. Please login.')
        return redirect(url_for('controllers.login'))
    return render_template('register.html')


@controllers.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, password=password).first()

        if not user:
            flash('Invalid credentials')
            return redirect(url_for('controllers.login'))

        if user.role == 'Blocked':
            flash('Your account has been blacklisted. Contact the admin.')
            return redirect(url_for('controllers.login'))

        if user.role == 'Trek Staff':
            profile = StaffProfile.query.filter_by(user_id=user.id).first()
            if not profile or profile.status in ['Pending', 'Blacklisted']:
                flash('Staff account is not approved yet')
                return redirect(url_for('controllers.login'))

        session.clear()
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
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='Trekker').count()
    total_staff = User.query.filter_by(role='Trek Staff').join(
        StaffProfile, User.id == StaffProfile.user_id
    ).filter(StaffProfile.status.in_(['Approved', 'Pending'])).count()
    total_bookings = Booking.query.count()
    recent_bookings = Booking.query.order_by(Booking.id.desc()).limit(5).all()
    return render_template(
        'admin_dashboard.html',
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
        recent_bookings=recent_bookings
    )


@controllers.route('/admin/treks', methods=['GET', 'POST'])
def admin_treks():
    if session.get('role') != 'Admin':
        return redirect(url_for('controllers.login'))
    q = request.form.get('q') or request.args.get('q', '')
    if q:
        treks = Trek.query.filter(
            or_(Trek.trek_name.like('%' + q + '%'), Trek.location.like('%' + q + '%'))
        ).all()
    else:
        treks = Trek.query.all()
    return render_template('admin_manage_treks.html', treks=treks, q=q)


@controllers.route('/admin/treks/add', methods=['GET', 'POST'])
def admin_treks_add():
    if session.get('role') != 'Admin':
        return redirect(url_for('controllers.login'))
    if request.method == 'POST':
        trek = Trek(
            trek_name=request.form.get('trek_name'),
            location=request.form.get('location'),
            difficulty=request.form.get('difficulty'),
            duration=request.form.get('duration'),
            available_slots=request.form.get('available_slots', type=int),
            assigned_staff_id=request.form.get('assign_staff', type=int),
            status=request.form.get('status') or 'Open',
            start_date=parse_date(request.form.get('start_date')),
            end_date=parse_date(request.form.get('end_date')),
            description=request.form.get('description')
        )
        db.session.add(trek)
        db.session.commit()
        return redirect(url_for('controllers.admin_treks'))
    staff_list = get_approved_staff_list()
    return render_template('admin_treks.html', staff_list=staff_list)


@controllers.route('/admin/treks/edit/<int:id>', methods=['GET', 'POST'])
def admin_treks_edit(id):
    if session.get('role') != 'Admin':
        return redirect(url_for('controllers.login'))
    trek = Trek.query.get_or_404(id)
    if request.method == 'POST':
        trek.trek_name = request.form.get('trek_name')
        trek.location = request.form.get('location')
        trek.difficulty = request.form.get('difficulty')
        trek.duration = request.form.get('duration')
        trek.available_slots = request.form.get('available_slots', type=int)
        trek.assigned_staff_id = request.form.get('assign_staff', type=int)
        trek.status = request.form.get('status') or trek.status
        trek.start_date = parse_date(request.form.get('start_date'))
        trek.end_date = parse_date(request.form.get('end_date'))
        trek.description = request.form.get('description')
        db.session.commit()
        return redirect(url_for('controllers.admin_treks'))
    staff_list = get_approved_staff_list()
    return render_template('admin_treks_edit.html', trek=trek, staff_list=staff_list)


@controllers.route('/admin/treks/delete/<int:id>', methods=['POST'])
def admin_treks_delete(id):
    if session.get('role') != 'Admin':
        return redirect(url_for('controllers.login'))
    trek = Trek.query.get_or_404(id)
    db.session.delete(trek)
    db.session.commit()
    return redirect(url_for('controllers.admin_treks'))


@controllers.route('/admin/staff', methods=['GET', 'POST'])
def admin_staff():
    if session.get('role') != 'Admin':
        return redirect(url_for('controllers.login'))
    if request.method == 'POST':
        staff_id = request.form.get('staff_id')
        status = request.form.get('status')
        profile = StaffProfile.query.get(staff_id)
        if profile:
            profile.status = status
            db.session.commit()
        return redirect(url_for('controllers.admin_staff'))
    q = request.args.get('q', '')
    if q:
        profiles = StaffProfile.query.filter(StaffProfile.name.like('%' + q + '%')).all()
    else:
        profiles = StaffProfile.query.all()
    staff_members = []
    for profile in profiles:
        user = User.query.get(profile.user_id)
        if user and user.role == 'Trek Staff':
            staff_members.append((user, profile))
    return render_template('admin_staff.html', staff_members=staff_members, q=q)


@controllers.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    if session.get('role') != 'Admin':
        return redirect(url_for('controllers.login'))
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        if user:
            if request.form.get('action') == 'toggle':
                if user.role == 'Trekker':
                    user.role = 'Blocked'
                else:
                    user.role = 'Trekker'
            else:
                user.role = request.form.get('role', user.role)
            db.session.commit()
        return redirect(url_for('controllers.admin_users'))
    q = request.args.get('q', '')
    if q:
        users = User.query.filter(User.username.like('%' + q + '%')).filter_by(role='Trekker').all()
    else:
        users = User.query.filter_by(role='Trekker').all()
    return render_template('admin_users.html', users=users, q=q)


@controllers.route('/admin/treks/assign/<int:trek_id>', methods=['POST'])
def admin_treks_assign(trek_id):
    if session.get('role') != 'Admin':
        return redirect(url_for('controllers.login'))
    trek = Trek.query.get_or_404(trek_id)
    trek.assigned_staff_id = request.form.get('staff_id', type=int)
    db.session.commit()
    return redirect(url_for('controllers.admin_treks'))


@controllers.route('/admin/bookings')
def admin_bookings():
    if session.get('role') != 'Admin':
        return redirect(url_for('controllers.login'))
    bookings = db.session.query(Booking, User, Trek).join(
        User, Booking.user_id == User.id
    ).join(Trek, Booking.trek_id == Trek.id).all()
    return render_template('admin_bookings.html', bookings=bookings)


# --- Placeholder role dashboards (built out fully in later milestones) ---

@controllers.route('/staff/dashboard')
def staff_dashboard():
    if session.get('role') != 'Trek Staff':
        return redirect(url_for('controllers.login'))
    return 'Trek Staff Dashboard - coming in Milestone 4'


@controllers.route('/trekker/dashboard')
def trekker_dashboard():
    if session.get('role') != 'Trekker':
        return redirect(url_for('controllers.login'))
    return 'Trekker Dashboard - coming in Milestone 5'


@controllers.app_errorhandler(404)
def page_not_found(error):
    return render_template('errors/404.html'), 404