import csv
import io
from flask import Blueprint, request, jsonify, session, Response
from routes.admin_routes import login_required, admin_required
from database.admin_service import (
    get_users, create_user, update_user, delete_user, toggle_user_status,
    change_user_password, get_orders_admin, get_order_details,
    update_order_status, delete_order, get_products_admin, create_product,
    update_product, delete_product, get_staging_records_admin,
    approve_staging_record, reject_staging_record, clear_staging_records,
    get_feedbacks_admin, update_feedback_status, delete_feedback,
    get_system_settings, update_system_setting, get_admin_dashboard_metrics,
    get_activity_logs, log_activity
)
from database.db_manager import execute_commit
from etl.etl_pipeline import run_etl
from config import config

admin_api_bp = Blueprint('admin_api', __name__, url_prefix='/api/admin')

# Apply login_required to all endpoints in this blueprint
@admin_api_bp.before_request
def check_authentication():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized. Please log in as an administrator.", "code": "UNAUTHORIZED"}), 401

# ============================================================================
# 1. METRICS & OVERVIEW
# ============================================================================

@admin_api_bp.route('/metrics', methods=['GET'])
def api_metrics():
    metrics = get_admin_dashboard_metrics()
    return jsonify({"success": True, "data": metrics})

# ============================================================================
# 2. USER MANAGEMENT APIS
# ============================================================================

@admin_api_bp.route('/users', methods=['GET'])
def api_get_users():
    search = request.args.get('q', '').strip()
    role = request.args.get('role', 'all')
    status = request.args.get('status', 'all')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    data = get_users(search=search, role=role, status=status, page=page, per_page=per_page)
    return jsonify({"success": True, "data": data})

@admin_api_bp.route('/users', methods=['POST'])
@admin_required
def api_create_user():
    data = request.get_json(silent=True) or request.form
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    full_name = data.get('full_name', '').strip()
    role = data.get('role', 'Analyst')
    status = data.get('status', 'Active')

    current_user = session.get('username', 'admin')
    success, msg = create_user(username, email, password, full_name, role=role, status=status, created_by=current_user)

    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

@admin_api_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def api_update_user(user_id):
    data = request.get_json(silent=True) or request.form
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    role = data.get('role', 'Analyst')
    status = data.get('status', 'Active')

    current_user = session.get('username', 'admin')
    success, msg = update_user(user_id, full_name, email, role, status, updated_by=current_user)

    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

@admin_api_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def api_toggle_user_status(user_id):
    current_user = session.get('username', 'admin')
    success, msg = toggle_user_status(user_id, updated_by=current_user)

    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

@admin_api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def api_delete_user(user_id):
    current_user = session.get('username', 'admin')
    success, msg = delete_user(user_id, deleted_by=current_user)

    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

# ============================================================================
# 3. ORDER & TRANSACTION MANAGEMENT APIS
# ============================================================================

@admin_api_bp.route('/orders', methods=['GET'])
def api_get_orders():
    search = request.args.get('q', '').strip()
    status = request.args.get('status', 'all')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 15))

    data = get_orders_admin(search=search, status=status, page=page, per_page=per_page)
    return jsonify({"success": True, "data": data})

@admin_api_bp.route('/orders/<int:order_key>', methods=['GET'])
def api_get_order_details(order_key):
    data = get_order_details(order_key)
    if not data:
        return jsonify({"success": False, "message": "Order not found."}), 404
    return jsonify({"success": True, "data": data})

@admin_api_bp.route('/orders/<int:order_key>/status', methods=['PUT'])
def api_update_order_status(order_key):
    data = request.get_json(silent=True) or request.form
    new_status = data.get('status', '').strip()

    current_user = session.get('username', 'admin')
    success, msg = update_order_status(order_key, new_status, username=current_user)

    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

@admin_api_bp.route('/orders/<int:order_key>', methods=['DELETE'])
@admin_required
def api_delete_order(order_key):
    current_user = session.get('username', 'admin')
    success, msg = delete_order(order_key, username=current_user)

    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

# ============================================================================
# 4. PRODUCT CATALOG MANAGEMENT APIS
# ============================================================================

@admin_api_bp.route('/products', methods=['GET'])
def api_get_products():
    search = request.args.get('q', '').strip()
    category = request.args.get('category', 'all')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 15))

    data = get_products_admin(search=search, category=category, page=page, per_page=per_page)
    return jsonify({"success": True, "data": data})

@admin_api_bp.route('/products', methods=['POST'])
@admin_required
def api_create_product():
    data = request.get_json(silent=True) or request.form
    prod_id = data.get('product_id', '').strip()
    name = data.get('product_name', '').strip()
    cat = data.get('category', '').strip()
    price = data.get('unit_price')

    current_user = session.get('username', 'admin')
    success, msg = create_product(prod_id, name, cat, price, username=current_user)

    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

@admin_api_bp.route('/products/<int:prod_key>', methods=['PUT'])
@admin_required
def api_update_product(prod_key):
    data = request.get_json(silent=True) or request.form
    name = data.get('product_name', '').strip()
    cat = data.get('category', '').strip()
    price = data.get('unit_price')

    current_user = session.get('username', 'admin')
    success, msg = update_product(prod_key, name, cat, price, username=current_user)

    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

@admin_api_bp.route('/products/<int:prod_key>', methods=['DELETE'])
@admin_required
def api_delete_product(prod_key):
    current_user = session.get('username', 'admin')
    success, msg = delete_product(prod_key, username=current_user)

    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

# ============================================================================
# 5. STAGING & ETL RECOVERY APIS
# ============================================================================

@admin_api_bp.route('/staging/<int:staging_id>/approve', methods=['POST'])
def api_approve_staging(staging_id):
    current_user = session.get('username', 'admin')
    success, msg = approve_staging_record(staging_id, username=current_user)

    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

@admin_api_bp.route('/staging/<int:staging_id>/reject', methods=['POST'])
def api_reject_staging(staging_id):
    data = request.get_json(silent=True) or request.form
    reason = data.get('reason', 'Manually rejected by administrator')
    current_user = session.get('username', 'admin')
    success, msg = reject_staging_record(staging_id, reason=reason, username=current_user)

    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

@admin_api_bp.route('/staging/clear', methods=['POST'])
@admin_required
def api_clear_staging():
    data = request.get_json(silent=True) or request.form
    status = data.get('status', 'all')
    current_user = session.get('username', 'admin')
    success, msg = clear_staging_records(status=status, username=current_user)

    return jsonify({"success": success, "message": msg})

@admin_api_bp.route('/run-etl', methods=['POST'])
def api_trigger_etl():
    """Triggers an ETL run on the sample dataset or uploaded transactions from admin."""
    current_user = session.get('username', 'admin')
    result = run_etl(config.SAMPLE_DATA_PATH, original_filename="sample_transactions.csv")
    log_activity(current_user, "Run ETL", "ETLHistory", result.get('batch_id'), f"Manual ETL trigger: {result.get('message')}")
    return jsonify(result)

# ============================================================================
# 6. FEEDBACK MANAGEMENT APIS
# ============================================================================

@admin_api_bp.route('/feedback/<int:feedback_id>/status', methods=['PUT'])
def api_update_feedback_status(feedback_id):
    data = request.get_json(silent=True) or request.form
    new_status = data.get('status', '').strip()
    current_user = session.get('username', 'admin')
    success, msg = update_feedback_status(feedback_id, new_status, username=current_user)

    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

@admin_api_bp.route('/feedback/<int:feedback_id>', methods=['DELETE'])
@admin_required
def api_delete_feedback(feedback_id):
    current_user = session.get('username', 'admin')
    success, msg = delete_feedback(feedback_id, username=current_user)

    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

# ============================================================================
# 7. PROFILE & SYSTEM SETTINGS APIS
# ============================================================================

@admin_api_bp.route('/profile', methods=['POST'])
def api_update_profile():
    data = request.get_json(silent=True) or request.form
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    user_id = session.get('user_id')

    if not full_name or not email:
        return jsonify({"success": False, "message": "Full Name and Email are required."}), 400

    execute_commit("UPDATE Users SET FullName = ?, Email = ? WHERE UserID = ?", (full_name, email, user_id))
    session['full_name'] = full_name
    session['email'] = email

    log_activity(session.get('username'), "Update Profile", "Users", str(user_id), f"Updated profile details.")
    return jsonify({"success": True, "message": "Profile updated successfully."})

@admin_api_bp.route('/change-password', methods=['POST'])
def api_change_password():
    data = request.get_json(silent=True) or request.form
    current_pw = data.get('current_password', '').strip()
    new_pw = data.get('new_password', '').strip()
    user_id = session.get('user_id')

    success, msg = change_user_password(user_id, current_pw, new_pw, changed_by=session.get('username'))
    if not success:
        return jsonify({"success": False, "message": msg}), 400
    return jsonify({"success": True, "message": msg})

@admin_api_bp.route('/settings', methods=['POST'])
@admin_required
def api_update_settings():
    data = request.get_json(silent=True) or request.form
    current_user = session.get('username', 'admin')

    for k, v in data.items():
        update_system_setting(k, v, username=current_user)

    return jsonify({"success": True, "message": "System configurations updated successfully."})

# ============================================================================
# 8. AUDIT LOG EXPORT
# ============================================================================

@admin_api_bp.route('/export-audit', methods=['GET'])
def api_export_audit():
    logs = get_activity_logs(limit=500)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['LogID', 'Timestamp', 'Username', 'Action', 'Entity', 'EntityID', 'Details', 'IPAddress'])

    for l in logs:
        writer.writerow([l['LogID'], l['CreatedAt'], l['Username'], l['Action'], l['Entity'], l['EntityID'], l['Details'], l['IPAddress']])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=marketmind_audit_trail.csv"}
    )
