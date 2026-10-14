from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database.db_manager import get_warehouse_stats, query_rows
from database.admin_service import (
    authenticate_user, get_user_by_id, get_users, get_orders_admin,
    get_products_admin, get_staging_records_admin, get_feedbacks_admin,
    get_activity_logs, get_system_settings, get_admin_dashboard_metrics,
    log_activity
)
from database.analytics_service import get_available_filter_options

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ============================================================================
# SECURITY DECORATORS
# ============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"success": False, "error": "Authentication required", "code": "UNAUTHORIZED"}), 401
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"success": False, "error": "Authentication required", "code": "UNAUTHORIZED"}), 401
            return redirect(url_for('admin.login', next=request.url))
        if session.get('role') != 'Admin':
            if request.path.startswith('/api/'):
                return jsonify({"success": False, "error": "Administrator privileges required", "code": "FORBIDDEN"}), 403
            return render_template('admin/access_denied.html', 
                                   error_title="Administrator Privileges Required",
                                   error_message="Your current role does not have administrative privileges for this page."), 403
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('admin.dashboard'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        result = authenticate_user(username, password)
        if result and 'error' in result:
            error = result['error']
        elif result:
            session['user_id'] = result['UserID']
            session['username'] = result['Username']
            session['role'] = result['Role']
            session['full_name'] = result['FullName']
            session['email'] = result['Email']
            session['avatar'] = result.get('Avatar', 'fa-user-tie')
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/admin'):
                return redirect(next_page)
            return redirect(url_for('admin.dashboard'))
        else:
            error = "Invalid username/email or password. Please try again."

    return render_template('admin/login.html', error=error)

@admin_bp.route('/quick-login')
def quick_login():
    """Convenient 1-click evaluator switch directly to the Admin Dashboard"""
    from database.admin_service import get_user_by_username
    target_role = request.args.get('role', 'admin').lower()
    target_username = 'analyst_priya' if target_role == 'analyst' else 'admin'
    user = get_user_by_username(target_username)
    if user:
        session['user_id'] = user['UserID']
        session['username'] = user['Username']
        session['role'] = user['Role']
        session['full_name'] = user['FullName']
        session['email'] = user['Email']
        session['avatar'] = user.get('Avatar', 'fa-user-tie')
        log_activity(user['Username'], "Quick Interface Switch", "Auth", str(user['UserID']), f"{user['Username']} switched interface to Admin Cockpit.")
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/logout')
def logout():
    username = session.get('username', 'User')
    if 'user_id' in session:
        log_activity(username, "User Logout", "Auth", str(session.get('user_id')), f"{username} logged out.")
    session.clear()
    flash("You have been securely signed out.", "info")
    return redirect(url_for('admin.login'))

# ============================================================================
# ADMIN DASHBOARD VIEWS
# ============================================================================

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin Cockpit Overview"""
    metrics = get_admin_dashboard_metrics()
    stats = get_warehouse_stats()
    return render_template('admin/dashboard.html', metrics=metrics, stats=stats)

@admin_bp.route('/users')
@login_required
def users():
    """User Management with Search, Filter & Pagination"""
    search = request.args.get('q', '').strip()
    role = request.args.get('role', 'all')
    status = request.args.get('status', 'all')
    page = int(request.args.get('page', 1))

    user_data = get_users(search=search, role=role, status=status, page=page, per_page=10)
    return render_template('admin/users.html', 
                           users=user_data['users'],
                           total=user_data['total'],
                           page=user_data['page'],
                           total_pages=user_data['total_pages'],
                           search=search,
                           role=role,
                           status=status)

@admin_bp.route('/orders')
@login_required
def orders():
    """Order & Transaction Management"""
    search = request.args.get('q', '').strip()
    status = request.args.get('status', 'all')
    page = int(request.args.get('page', 1))

    order_data = get_orders_admin(search=search, status=status, page=page, per_page=15)
    return render_template('admin/orders.html',
                           orders=order_data['orders'],
                           total=order_data['total'],
                           page=order_data['page'],
                           total_pages=order_data['total_pages'],
                           search=search,
                           status=status)

@admin_bp.route('/products')
@login_required
def products():
    """Product Catalog Management"""
    search = request.args.get('q', '').strip()
    category = request.args.get('category', 'all')
    page = int(request.args.get('page', 1))

    prod_data = get_products_admin(search=search, category=category, page=page, per_page=15)
    filter_opts = get_available_filter_options()

    return render_template('admin/products.html',
                           products=prod_data['products'],
                           total=prod_data['total'],
                           page=prod_data['page'],
                           total_pages=prod_data['total_pages'],
                           categories=filter_opts['categories'],
                           search=search,
                           category=category)

@admin_bp.route('/etl-management')
@login_required
def etl_management():
    """ETL Batch History & Staging Rejections Management"""
    status = request.args.get('status', 'all')
    batch_id = request.args.get('batch_id', 'all')
    page = int(request.args.get('page', 1))

    staging_data = get_staging_records_admin(status=status, batch_id=batch_id, page=page, per_page=15)
    etl_history = query_rows("SELECT * FROM ETLHistory ORDER BY CreatedAt DESC LIMIT 20")

    return render_template('admin/etl_management.html',
                           records=staging_data['records'],
                           total=staging_data['total'],
                           page=staging_data['page'],
                           total_pages=staging_data['total_pages'],
                           batches=staging_data['batches'],
                           etl_history=etl_history,
                           status=status,
                           batch_id=batch_id)

@admin_bp.route('/feedback')
@login_required
def feedback():
    """Viva & Evaluator Feedback Management"""
    status = request.args.get('status', 'all')
    rating = request.args.get('rating', 'all')
    search = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))

    fb_data = get_feedbacks_admin(status=status, rating=rating, search=search, page=page, per_page=15)
    return render_template('admin/feedback.html',
                           feedbacks=fb_data['feedbacks'],
                           total=fb_data['total'],
                           page=fb_data['page'],
                           total_pages=fb_data['total_pages'],
                           search=search,
                           status=status,
                           rating=rating)

@admin_bp.route('/reports')
@login_required
def reports():
    """System Audit Reports & Data Warehouse Analytics"""
    search = request.args.get('q', '').strip()
    logs = get_activity_logs(limit=50, search=search)
    stats = get_warehouse_stats()
    metrics = get_admin_dashboard_metrics()
    return render_template('admin/reports.html', logs=logs, stats=stats, metrics=metrics, search=search)

@admin_bp.route('/settings')
@login_required
def settings():
    """Admin Profile & System Settings"""
    user = get_user_by_id(session['user_id'])
    settings = get_system_settings()
    return render_template('admin/settings.html', user=user, settings=settings)
