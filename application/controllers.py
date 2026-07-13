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
        user = User(username=username, password=password, role=role, contact_details=contact_details or '')
        db.session.add(user)
        db.session.commit()
        if role == 'Trek Staff':
            profile = StaffProfile(user_id=user.id, name=name or '', contact_details=contact_details or '', status='Pending')
            db.session.add(profile)
            db.session.commit()
        flash('Registration successful', 'success')
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
                flash('Staff account is not approved')
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
    total_staff = User.query.filter_by(role='Trek Staff').join(StaffProfile, User.id == StaffProfile.user_id).filter(StaffProfile.status.in_(['Approved', 'Pending'])).count()
    total_bookings = Booking.query.count()
    recent_bookings = Booking.query.order_by(Booking.id.desc()).limit(5).all()
    return render_template('admin_dashboard.html', total_treks=total_treks, total_users=total_users, total_staff=total_staff, total_bookings=total_bookings, recent_bookings=recent_bookings)


@controllers.route('/admin/treks', methods=['GET', 'POST'])
def admin_treks():
    if session.get('role') != 'Admin':
        return redirect(url_for('controllers.login'))
    q = request.form.get('q') or request.args.get('q', '')
    if q:
        filters = [Trek.trek_name.like('%' + q + '%'), Trek.location.like('%' + q + '%')]
        if q.isdigit():
            filters.append(Trek.id == int(q))
        treks = Trek.query.filter(or_(*filters)).all()
    else:
        treks = Trek.query.all()
    return render_template('admin_manage_treks.html', treks=treks, q=q)


@controllers.route('/admin/treks/add', methods=['GET', 'POST'])
def admin_treks_add():
    if session.get('role') != 'Admin':
        return redirect(url_for('controllers.login'))
    if request.method == 'POST':
        slots = request.form.get('available_slots', type=int)
        trek = Trek(
            trek_name=request.form.get('trek_name'),
            location=request.form.get('location'),
            difficulty=request.form.get('difficulty'),
            duration=request.form.get('duration'),
            available_slots=max(0, slots) if slots is not None else 0,
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
        slots = request.form.get('available_slots', type=int)
        trek.available_slots = max(0, slots) if slots is not None else trek.available_slots
        trek.assigned_staff_id = request.form.get('assign_staff', type=int)
        trek.status = request.form.get('status') or trek.status
        trek.start_date = parse_date(request.form.get('start_date'))
        trek.end_date = parse_date(request.form.get('end_date'))
        trek.description = request.form.get('description')
        db.session.commit()
        return redirect(url_for('controllers.admin_treks'))
    staff_list = get_approved_staff_list()
    return render_template('admin_trek_edit.html', trek=trek, staff_list=staff_list)


@controllers.route('/admin/treks/delete/<int:id>', methods=['POST'])
def admin_treks_delete(id):
    if session.get('role') != 'Admin':
        return redirect(url_for('controllers.login'))
    trek = Trek.query.get_or_404(id)
    if Booking.query.filter_by(trek_id=id).first():
        flash('Cannot remove: this trek has existing bookings. Close it instead of deleting.')
        return redirect(url_for('controllers.admin_treks'))
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
        filters = [StaffProfile.name.like('%' + q + '%')]
        if q.isdigit():
            filters.append(StaffProfile.id == int(q))
        profiles = StaffProfile.query.filter(or_(*filters)).all()
    else:
        profiles = StaffProfile.query.all()
    staff_members = []
    for profile in profiles:
        user = User.query.get(profile.user_id)
        if user and user.role == 'Trek Staff':
            staff_members.append((user, profile))
    return render_template('admin_staff.html', staff_members=staff_members, q=q)


@controllers.route('/admin/staff/add', methods=['GET', 'POST'])
def admin_staff_add():
    if session.get('role') != 'Admin':
        return redirect(url_for('controllers.login'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        contact_details = request.form.get('contact_details')
        if not username or not password:
            flash('Username and password are required')
            return redirect(url_for('controllers.admin_staff_add'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('controllers.admin_staff_add'))
        user = User(username=username, password=password, role='Trek Staff', contact_details=contact_details or '')
        db.session.add(user)
        db.session.commit()
        profile = StaffProfile(user_id=user.id, name=name or username, contact_details=contact_details or '', status='Approved')
        db.session.add(profile)
        db.session.commit()
        flash('Staff member added and approved', 'success')
        return redirect(url_for('controllers.admin_staff'))
    return render_template('admin_staff_add.html')


@controllers.route('/admin/staff/delete/<int:staff_id>', methods=['POST'])
def admin_staff_delete(staff_id):
    if session.get('role') != 'Admin':
        return redirect(url_for('controllers.login'))
    profile = StaffProfile.query.get_or_404(staff_id)
    if Trek.query.filter_by(assigned_staff_id=profile.user_id).first():
        flash('Cannot remove: this staff member is still assigned to one or more treks. Unassign first.')
        return redirect(url_for('controllers.admin_staff'))
    user = User.query.get(profile.user_id)
    db.session.delete(profile)
    if user:
        db.session.delete(user)
    db.session.commit()
    flash('Staff member removed', 'success')
    return redirect(url_for('controllers.admin_staff'))


@controllers.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def admin_users_delete(user_id):
    if session.get('role') != 'Admin':
        return redirect(url_for('controllers.login'))
    user = User.query.get_or_404(user_id)
    if Booking.query.filter_by(user_id=user_id).first():
        flash('Cannot remove: this user has existing bookings. Blacklist instead.')
        return redirect(url_for('controllers.admin_users'))
    db.session.delete(user)
    db.session.commit()
    flash('User removed', 'success')
    return redirect(url_for('controllers.admin_users'))


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
        filters = [User.username.like('%' + q + '%')]
        if q.isdigit():
            filters.append(User.id == int(q))
        users = User.query.filter(or_(*filters)).filter_by(role='Trekker').all()
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
    bookings = db.session.query(Booking, User, Trek).join(User, Booking.user_id == User.id).join(Trek, Booking.trek_id == Trek.id).all()
    return render_template('admin_bookings.html', bookings=bookings)


@controllers.route('/staff/dashboard')
def staff_dashboard():
    if session.get('role') != 'Trek Staff':
        return redirect(url_for('controllers.login'))
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    profile = StaffProfile.query.filter_by(user_id=user_id).first()
    assigned_treks = Trek.query.filter_by(assigned_staff_id=user_id).all()
    trek_data = []
    total_participants = 0
    open_treks_count = 0
    for trek in assigned_treks:
        participant_count = Booking.query.filter_by(trek_id=trek.id, status='Booked').count()
        trek_data.append({'trek': trek, 'participant_count': participant_count})
        total_participants += participant_count
        if trek.status == 'Open':
            open_treks_count += 1
    return render_template(
        'staff_dashboard.html',
        user=user,
        profile=profile,
        trek_data=trek_data,
        total_participants=total_participants,
        open_treks_count=open_treks_count
    )


@controllers.route('/staff/profile/update', methods=['POST'])
def staff_profile_update():
    if session.get('role') != 'Trek Staff':
        return redirect(url_for('controllers.login'))
    user_id = session.get('user_id')
    profile = StaffProfile.query.filter_by(user_id=user_id).first()
    if profile:
        profile.name = request.form.get('name', profile.name)
        profile.contact_details = request.form.get('contact_details', profile.contact_details)
        db.session.commit()
    return redirect(url_for('controllers.staff_dashboard'))


@controllers.route('/staff/trek/manage/<int:trek_id>')
def staff_trek_manage(trek_id):
    if session.get('role') != 'Trek Staff':
        return redirect(url_for('controllers.login'))
    user_id = session.get('user_id')
    trek = Trek.query.get_or_404(trek_id)
    if trek.assigned_staff_id != user_id:
        flash('You are not assigned to this trek.')
        return redirect(url_for('controllers.staff_dashboard'))
    bookings = Booking.query.filter_by(trek_id=trek_id).all()
    participants = []
    for booking in bookings:
        user = User.query.get(booking.user_id)
        if user:
            participants.append({'user': user, 'booking': booking})
    return render_template('staff_manage_trek.html', trek=trek, participants=participants)


@controllers.route('/staff/trek/update-status/<int:trek_id>', methods=['POST'])
def staff_trek_update_status(trek_id):
    if session.get('role') != 'Trek Staff':
        return redirect(url_for('controllers.login'))
    user_id = session.get('user_id')
    trek = Trek.query.get_or_404(trek_id)
    if trek.assigned_staff_id != user_id:
        flash('You are not assigned to this trek.')
        return redirect(url_for('controllers.staff_dashboard'))
    trek.status = request.form.get('status', trek.status)
    new_slots = request.form.get('available_slots', type=int)
    if new_slots is not None:
        trek.available_slots = max(0, new_slots)
    if trek.status == 'Completed':
        Booking.query.filter_by(trek_id=trek_id, status='Booked').update(
            {'status': 'Completed', 'completed_on': db.func.current_timestamp()}
        )
    db.session.commit()
    flash('Trek updated successfully.', 'success')
    return redirect(url_for('controllers.staff_trek_manage', trek_id=trek_id))


@controllers.route('/staff/trek/<int:trek_id>/participant/<int:booking_id>/cancel', methods=['POST'])
def staff_cancel_participant(trek_id, booking_id):
    if session.get('role') != 'Trek Staff':
        return redirect(url_for('controllers.login'))
    user_id = session.get('user_id')
    trek = Trek.query.get_or_404(trek_id)
    if trek.assigned_staff_id != user_id:
        flash('You are not assigned to this trek.')
        return redirect(url_for('controllers.staff_dashboard'))
    booking = Booking.query.get_or_404(booking_id)
    if booking.trek_id != trek_id:
        flash('Invalid booking for this trek.')
        return redirect(url_for('controllers.staff_trek_manage', trek_id=trek_id))
    if trek.status in ['Started', 'Ongoing', 'Completed']:
        flash('Cannot remove a participant once the trek has started.')
        return redirect(url_for('controllers.staff_trek_manage', trek_id=trek_id))
    if booking.status == 'Booked':
        booking.status = 'Cancelled'
        trek.available_slots += 1
        db.session.commit()
        flash('Participant removed from the trek.', 'success')
    return redirect(url_for('controllers.staff_trek_manage', trek_id=trek_id))


@controllers.route('/trekker/dashboard')
def trekker_dashboard():
    if session.get('role') != 'Trekker':
        return redirect(url_for('controllers.login'))
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    query = Trek.query.filter_by(status='Open')
    location = request.args.get('location')
    difficulty = request.args.get('difficulty')
    if location:
        query = query.filter(Trek.location.ilike('%' + location + '%'))
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    treks = query.all()
    bookings = Booking.query.filter_by(user_id=user_id).filter(Booking.status.in_(['Booked', 'Cancelled'])).all()
    return render_template('trekker_dashboard.html', user=user, treks=treks, bookings=bookings)


@controllers.route('/trekker/profile/update', methods=['POST'])
def trekker_profile_update():
    if session.get('role') != 'Trekker':
        return redirect(url_for('controllers.login'))
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if user:
        username = request.form.get('username')
        contact_details = request.form.get('contact_details')
        if username and username != user.username:
            existing = User.query.filter_by(username=username).first()
            if existing:
                flash('That username is already taken. Please choose another.')
                return redirect(url_for('controllers.trekker_dashboard'))
            user.username = username
        if contact_details is not None:
            user.contact_details = contact_details
        db.session.commit()
        flash('Profile updated successfully.', 'success')
    return redirect(url_for('controllers.trekker_dashboard'))


@controllers.route('/trekker/book/<int:trek_id>', methods=['POST'])
def trekker_book(trek_id):
    if session.get('role') != 'Trekker':
        return redirect(url_for('controllers.login'))
    trek = Trek.query.get_or_404(trek_id)
    if trek.status != 'Open' or trek.available_slots <= 0:
        flash('This trek is not available right now.')
        return redirect(url_for('controllers.trekker_dashboard'))
    existing_booking = Booking.query.filter_by(user_id=session.get('user_id'), trek_id=trek_id, status='Booked').first()
    if existing_booking:
        flash('You already booked this trek.')
        return redirect(url_for('controllers.trekker_dashboard'))
    booking = Booking(user_id=session.get('user_id'), trek_id=trek_id, booking_date=db.func.current_timestamp(), status='Booked')
    db.session.add(booking)
    trek.available_slots -= 1
    db.session.commit()
    flash('Booking successful.', 'success')
    return redirect(url_for('controllers.trekker_dashboard'))


@controllers.route('/trekker/booking/cancel/<int:booking_id>', methods=['POST'])
def trekker_cancel_booking(booking_id):
    if session.get('role') != 'Trekker':
        return redirect(url_for('controllers.login'))
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != session.get('user_id'):
        return redirect(url_for('controllers.trekker_dashboard'))
    trek = Trek.query.get(booking.trek_id)
    if trek and trek.status != 'Started' and trek.status != 'Ongoing' and trek.status != 'Completed':
        booking.status = 'Cancelled'
        if trek:
            trek.available_slots += 1
        db.session.commit()
        flash('Booking cancelled.', 'success')
    else:
        flash('This booking cannot be cancelled now.')
    return redirect(url_for('controllers.trekker_dashboard'))


@controllers.route('/trekker/history')
def trekker_history():
    if session.get('role') != 'Trekker':
        return redirect(url_for('controllers.login'))
    user_id = session.get('user_id')
    bookings = Booking.query.filter_by(user_id=user_id, status='Completed').order_by(Booking.completed_on.desc()).all()
    return render_template('trekker_history.html', bookings=bookings)


@controllers.before_request
def check_access():
    if request.path.startswith('/admin') and session.get('role') != 'Admin' and request.path != '/login':
        return redirect(url_for('controllers.login'))
    if request.path.startswith('/staff') and session.get('role') != 'Trek Staff' and request.path != '/login':
        return redirect(url_for('controllers.login'))
    if request.path.startswith('/trekker') and session.get('role') != 'Trekker' and request.path != '/login':
        return redirect(url_for('controllers.login'))


@controllers.app_errorhandler(404)
def page_not_found(error):
    return render_template('errors/404.html'), 404


@controllers.app_errorhandler(403)
def forbidden(error):
    return redirect(url_for('controllers.login'))


@controllers.context_processor
def inject_user_context():
    return {'current_role': session.get('role')}