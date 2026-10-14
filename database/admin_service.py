import math
import sqlite3
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database.db_manager import get_db_connection, query_rows, query_scalar, execute_commit

# ============================================================================
# 1. AUTHENTICATION & USER MANAGEMENT
# ============================================================================

def authenticate_user(username_or_email, password):
    """
    Validates user credentials against hashed password.
    Returns user dict on success, None on invalid credentials.
    """
    if not username_or_email or not password:
        return None
    
    query = """
        SELECT UserID, Username, Email, PasswordHash, FullName, Role, Status, Avatar, CreatedAt, LastLogin
        FROM Users
        WHERE LOWER(Username) = LOWER(?) OR LOWER(Email) = LOWER(?)
    """
    rows = query_rows(query, (username_or_email.strip(), username_or_email.strip()))
    if not rows:
        return None
    
    user = rows[0]
    if user['Status'] != 'Active':
        return {"error": "Account is suspended. Please contact the administrator."}
    
    if check_password_hash(user['PasswordHash'], password):
        # Update last login timestamp
        execute_commit("UPDATE Users SET LastLogin = CURRENT_TIMESTAMP WHERE UserID = ?", (user['UserID'],))
        log_activity(user['Username'], "User Login", "Auth", str(user['UserID']), f"User {user['Username']} successfully logged in.")
        # Return user dict without password hash
        user_data = dict(user)
        del user_data['PasswordHash']
        return user_data
    
    return None

def get_user_by_id(user_id):
    """Retrieves user info without password hash."""
    query = """
        SELECT UserID, Username, Email, FullName, Role, Status, Avatar, CreatedAt, LastLogin
        FROM Users
        WHERE UserID = ?
    """
    rows = query_rows(query, (user_id,))
    return rows[0] if rows else None

def get_user_by_username(username):
    """Retrieves user by username."""
    query = """
        SELECT UserID, Username, Email, FullName, Role, Status, Avatar, CreatedAt, LastLogin
        FROM Users
        WHERE LOWER(Username) = LOWER(?)
    """
    rows = query_rows(query, (username.strip(),))
    return rows[0] if rows else None

def get_users(search=None, role=None, status=None, page=1, per_page=10):
    """Retrieves paginated user accounts with filtering."""
    where_parts = ["1=1"]
    params = []

    if search:
        where_parts.append("(Username LIKE ? OR Email LIKE ? OR FullName LIKE ?)")
        s_term = f"%{search.strip()}%"
        params.extend([s_term, s_term, s_term])
    
    if role and role.lower() != 'all':
        where_parts.append("Role = ?")
        params.append(role)

    if status and status.lower() != 'all':
        where_parts.append("Status = ?")
        params.append(status)

    where_sql = " AND ".join(where_parts)

    count_sql = f"SELECT COUNT(*) FROM Users WHERE {where_sql}"
    total_count = query_scalar(count_sql, params if params else None) or 0

    page = max(1, int(page))
    offset = (page - 1) * per_page
    total_pages = max(1, math.ceil(total_count / per_page))

    sql = f"""
        SELECT UserID, Username, Email, FullName, Role, Status, Avatar, CreatedAt, LastLogin
        FROM Users
        WHERE {where_sql}
        ORDER BY CreatedAt DESC
        LIMIT ? OFFSET ?
    """
    list_params = list(params) + [per_page, offset]
    users = query_rows(sql, list_params)

    return {
        "users": users,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }

def create_user(username, email, password, full_name, role='Analyst', status='Active', created_by='admin'):
    """Creates a new user with securely hashed password."""
    username = username.strip()
    email = email.strip()
    full_name = full_name.strip()

    if not username or not email or not password or not full_name:
        return False, "All fields (Username, Email, Password, Full Name) are required."

    # Validate uniqueness
    existing = query_rows("SELECT UserID FROM Users WHERE LOWER(Username) = LOWER(?) OR LOWER(Email) = LOWER(?)", (username, email))
    if existing:
        return False, "Username or Email already exists in the system."

    valid_roles = ['Admin', 'Analyst', 'Viewer']
    if role not in valid_roles:
        role = 'Analyst'

    pw_hash = generate_password_hash(password)
    user_id = execute_commit("""
        INSERT INTO Users (Username, Email, PasswordHash, FullName, Role, Status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, email, pw_hash, full_name, role, status))

    log_activity(created_by, "Create User", "Users", str(user_id), f"Created account '{username}' with role '{role}'.")
    return True, f"User {username} successfully registered."

def update_user(user_id, full_name, email, role, status, updated_by='admin'):
    """Updates user metadata and role."""
    user = get_user_by_id(user_id)
    if not user:
        return False, "User not found."

    email = email.strip()
    full_name = full_name.strip()

    # Check email conflict
    conflict = query_rows("SELECT UserID FROM Users WHERE LOWER(Email) = LOWER(?) AND UserID != ?", (email, user_id))
    if conflict:
        return False, "Email address is already in use by another user."

    execute_commit("""
        UPDATE Users
        SET FullName = ?, Email = ?, Role = ?, Status = ?
        WHERE UserID = ?
    """, (full_name, email, role, status, user_id))

    log_activity(updated_by, "Update User", "Users", str(user_id), f"Updated profile for '{user['Username']}' (Role: {role}, Status: {status}).")
    return True, f"User {user['Username']} updated successfully."

def toggle_user_status(user_id, updated_by='admin'):
    """Toggles user status between Active and Suspended."""
    user = get_user_by_id(user_id)
    if not user:
        return False, "User not found."

    new_status = 'Suspended' if user['Status'] == 'Active' else 'Active'
    execute_commit("UPDATE Users SET Status = ? WHERE UserID = ?", (new_status, user_id))
    log_activity(updated_by, "Toggle User Status", "Users", str(user_id), f"Changed status of '{user['Username']}' to '{new_status}'.")
    return True, f"User '{user['Username']}' is now {new_status}."

def delete_user(user_id, deleted_by='admin'):
    """Deletes a user account (cannot delete the last admin)."""
    user = get_user_by_id(user_id)
    if not user:
        return False, "User not found."

    if user['Role'] == 'Admin':
        admin_count = query_scalar("SELECT COUNT(*) FROM Users WHERE Role = 'Admin'") or 0
        if admin_count <= 1:
            return False, "Cannot delete the sole Administrator account."

    execute_commit("DELETE FROM Users WHERE UserID = ?", (user_id,))
    log_activity(deleted_by, "Delete User", "Users", str(user_id), f"Deleted account '{user['Username']}'.")
    return True, f"User {user['Username']} deleted successfully."

def change_user_password(user_id, old_password, new_password, is_admin_override=False, changed_by=None):
    """Updates user password with old password verification unless admin override."""
    query = "SELECT PasswordHash, Username FROM Users WHERE UserID = ?"
    rows = query_rows(query, (user_id,))
    if not rows:
        return False, "User not found."

    user = rows[0]
    if not is_admin_override:
        if not check_password_hash(user['PasswordHash'], old_password):
            return False, "Current password does not match."

    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long."

    new_hash = generate_password_hash(new_password)
    execute_commit("UPDATE Users SET PasswordHash = ? WHERE UserID = ?", (new_hash, user_id))

    actor = changed_by or user['Username']
    log_activity(actor, "Change Password", "Users", str(user_id), f"Password updated for user '{user['Username']}'.")
    return True, "Password changed successfully."

# ============================================================================
# 2. ACTIVITY AUDIT LOGGING
# ============================================================================

def log_activity(username, action, entity, entity_id=None, details=None, ip_address='127.0.0.1'):
    """Inserts a structured security / action audit record."""
    try:
        execute_commit("""
            INSERT INTO ActivityLogs (Username, Action, Entity, EntityID, Details, IPAddress)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username or 'System', action, entity, str(entity_id or ''), details or '', ip_address))
    except Exception as e:
        print(f"Error writing activity log: {e}")

def get_activity_logs(limit=30, search=None):
    """Retrieves recent activity logs."""
    where_parts = ["1=1"]
    params = []

    if search:
        where_parts.append("(Username LIKE ? OR Action LIKE ? OR Entity LIKE ? OR Details LIKE ?)")
        s = f"%{search.strip()}%"
        params.extend([s, s, s, s])

    where_sql = " AND ".join(where_parts)
    sql = f"""
        SELECT LogID, Username, Action, Entity, EntityID, Details, IPAddress, CreatedAt
        FROM ActivityLogs
        WHERE {where_sql}
        ORDER BY CreatedAt DESC, LogID DESC
        LIMIT ?
    """
    params.append(limit)
    return query_rows(sql, params)

# ============================================================================
# 3. ORDER & TRANSACTION MANAGEMENT
# ============================================================================

def get_orders_admin(search=None, status=None, page=1, per_page=15):
    """Retrieves paginated orders with customer details and line-item totals."""
    where_parts = ["1=1"]
    params = []

    if search:
        where_parts.append("(o.InvoiceNo LIKE ? OR c.CustomerName LIKE ? OR c.CustomerID LIKE ?)")
        s = f"%{search.strip()}%"
        params.extend([s, s, s])

    if status and status.lower() != 'all':
        where_parts.append("o.OrderStatus = ?")
        params.append(status)

    where_sql = " AND ".join(where_parts)

    count_sql = f"""
        SELECT COUNT(DISTINCT o.OrderKey)
        FROM DimOrder o
        LEFT JOIN FactSales f ON o.OrderKey = f.OrderKey
        LEFT JOIN DimCustomer c ON f.CustomerKey = c.CustomerKey
        WHERE {where_sql}
    """
    total_count = query_scalar(count_sql, params if params else None) or 0

    page = max(1, int(page))
    offset = (page - 1) * per_page
    total_pages = max(1, math.ceil(total_count / per_page))

    sql = f"""
        SELECT 
            o.OrderKey,
            o.InvoiceNo,
            o.OrderDate,
            o.OrderStatus,
            o.TotalItems,
            o.TotalOrderValue,
            COALESCE(c.CustomerName, 'Guest Customer') AS CustomerName,
            COALESCE(c.CustomerID, 'N/A') AS CustomerID,
            COALESCE(c.Country, 'India') AS Country,
            COUNT(f.SalesKey) AS LineItemsCount,
            ROUND(SUM(f.TotalAmount), 2) AS CalculatedTotal
        FROM DimOrder o
        LEFT JOIN FactSales f ON o.OrderKey = f.OrderKey
        LEFT JOIN DimCustomer c ON f.CustomerKey = c.CustomerKey
        WHERE {where_sql}
        GROUP BY o.OrderKey, o.InvoiceNo, o.OrderDate, o.OrderStatus, o.TotalItems, o.TotalOrderValue, c.CustomerName, c.CustomerID, c.Country
        ORDER BY o.OrderDate DESC, o.OrderKey DESC
        LIMIT ? OFFSET ?
    """
    list_params = list(params) + [per_page, offset]
    orders = query_rows(sql, list_params)

    return {
        "orders": orders,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }

def get_order_details(order_id):
    """Retrieves full order information including all FactSales line items and product details."""
    order_query = """
        SELECT 
            o.OrderKey, o.InvoiceNo, o.OrderDate, o.OrderStatus, o.TotalItems, o.TotalOrderValue,
            c.CustomerKey, c.CustomerID, c.CustomerName, c.Country, c.Segment
        FROM DimOrder o
        LEFT JOIN FactSales f ON o.OrderKey = f.OrderKey
        LEFT JOIN DimCustomer c ON f.CustomerKey = c.CustomerKey
        WHERE o.OrderKey = ? OR o.InvoiceNo = ?
        LIMIT 1
    """
    order_rows = query_rows(order_query, (order_id, str(order_id)))
    if not order_rows:
        return None

    order_info = order_rows[0]

    # Get line items
    items_query = """
        SELECT 
            f.SalesKey,
            p.ProductID,
            p.ProductName,
            p.Category,
            f.Quantity,
            f.UnitPrice,
            f.DiscountAmount,
            f.TotalAmount,
            f.ProfitMargin
        FROM FactSales f
        JOIN DimProduct p ON f.ProductKey = p.ProductKey
        WHERE f.OrderKey = ?
        ORDER BY f.SalesKey ASC
    """
    items = query_rows(items_query, (order_info['OrderKey'],))

    return {
        "order": order_info,
        "items": items,
        "items_count": len(items),
        "total_calculated": sum(i['TotalAmount'] for i in items)
    }

def update_order_status(order_key, new_status, username='admin'):
    """Updates order status (e.g. Completed, Pending, Shipped, Cancelled, Refunded)."""
    valid_statuses = ['Completed', 'Pending', 'Shipped', 'Cancelled', 'Refunded']
    if new_status not in valid_statuses:
        return False, f"Invalid order status '{new_status}'. Allowed: {', '.join(valid_statuses)}."

    order = query_rows("SELECT InvoiceNo FROM DimOrder WHERE OrderKey = ?", (order_key,))
    if not order:
        return False, "Order not found."

    execute_commit("UPDATE DimOrder SET OrderStatus = ? WHERE OrderKey = ?", (new_status, order_key))
    log_activity(username, "Update Order Status", "DimOrder", str(order_key), f"Order {order[0]['InvoiceNo']} status changed to '{new_status}'.")
    return True, f"Order status updated to {new_status}."

def delete_order(order_key, username='admin'):
    """Deletes order and cascading FactSales records."""
    order = query_rows("SELECT InvoiceNo FROM DimOrder WHERE OrderKey = ?", (order_key,))
    if not order:
        return False, "Order not found."

    invoice = order[0]['InvoiceNo']
    # Delete fact records first (or foreign key cascade)
    execute_commit("DELETE FROM FactSales WHERE OrderKey = ?", (order_key,))
    execute_commit("DELETE FROM DimOrder WHERE OrderKey = ?", (order_key,))

    log_activity(username, "Delete Order", "DimOrder", str(order_key), f"Deleted order invoice {invoice} and its fact line items.")
    return True, f"Order {invoice} and associated fact line items deleted."

# ============================================================================
# 4. PRODUCT CATALOG MANAGEMENT
# ============================================================================

def get_products_admin(search=None, category=None, page=1, per_page=15):
    """Retrieves catalog products with sales telemetry and pagination."""
    where_parts = ["1=1"]
    params = []

    if search:
        where_parts.append("(p.ProductID LIKE ? OR p.ProductName LIKE ?)")
        s = f"%{search.strip()}%"
        params.extend([s, s])

    if category and category.lower() != 'all':
        where_parts.append("p.Category = ?")
        params.append(category)

    where_sql = " AND ".join(where_parts)

    count_sql = f"SELECT COUNT(*) FROM DimProduct p WHERE {where_sql}"
    total_count = query_scalar(count_sql, params if params else None) or 0

    page = max(1, int(page))
    offset = (page - 1) * per_page
    total_pages = max(1, math.ceil(total_count / per_page))

    sql = f"""
        SELECT 
            p.ProductKey,
            p.ProductID,
            p.ProductName,
            p.Category,
            p.UnitPrice,
            p.CreatedAt,
            COALESCE(SUM(f.Quantity), 0) AS UnitsSold,
            COALESCE(ROUND(SUM(f.TotalAmount), 2), 0.0) AS RevenueGenerated,
            COUNT(DISTINCT f.OrderKey) AS OrdersCount
        FROM DimProduct p
        LEFT JOIN FactSales f ON p.ProductKey = f.ProductKey
        WHERE {where_sql}
        GROUP BY p.ProductKey, p.ProductID, p.ProductName, p.Category, p.UnitPrice, p.CreatedAt
        ORDER BY RevenueGenerated DESC, p.ProductKey ASC
        LIMIT ? OFFSET ?
    """
    list_params = list(params) + [per_page, offset]
    products = query_rows(sql, list_params)

    return {
        "products": products,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }

def create_product(product_id, product_name, category, unit_price, username='admin'):
    """Adds a new SKU to DimProduct."""
    product_id = product_id.strip()
    product_name = product_name.strip()
    category = category.strip()

    try:
        unit_price = float(unit_price)
        if unit_price <= 0:
            return False, "Unit price must be greater than zero."
    except (ValueError, TypeError):
        return False, "Invalid unit price value."

    # Check uniqueness
    existing = query_rows("SELECT ProductKey FROM DimProduct WHERE LOWER(ProductID) = LOWER(?)", (product_id,))
    if existing:
        return False, f"Product ID '{product_id}' already exists."

    product_key = execute_commit("""
        INSERT INTO DimProduct (ProductID, ProductName, Category, UnitPrice)
        VALUES (?, ?, ?, ?)
    """, (product_id, product_name, category, unit_price))

    log_activity(username, "Create Product", "DimProduct", str(product_key), f"Added new product '{product_name}' (SKU: {product_id}, Category: {category}, Price: ₹{unit_price:.2f}).")
    return True, f"Product '{product_name}' successfully added."

def update_product(product_key, product_name, category, unit_price, username='admin'):
    """Updates product attributes in DimProduct."""
    prod = query_rows("SELECT ProductID, ProductName FROM DimProduct WHERE ProductKey = ?", (product_key,))
    if not prod:
        return False, "Product not found."

    product_name = product_name.strip()
    category = category.strip()
    try:
        unit_price = float(unit_price)
        if unit_price <= 0:
            return False, "Unit price must be greater than zero."
    except (ValueError, TypeError):
        return False, "Invalid unit price value."

    execute_commit("""
        UPDATE DimProduct
        SET ProductName = ?, Category = ?, UnitPrice = ?
        WHERE ProductKey = ?
    """, (product_name, category, unit_price, product_key))

    log_activity(username, "Update Product", "DimProduct", str(product_key), f"Updated product {prod[0]['ProductID']}: '{product_name}' (₹{unit_price:.2f}).")
    return True, f"Product '{product_name}' updated successfully."

def delete_product(product_key, username='admin'):
    """Deletes a product if not referenced by sales facts."""
    prod = query_rows("SELECT ProductID, ProductName FROM DimProduct WHERE ProductKey = ?", (product_key,))
    if not prod:
        return False, "Product not found."

    sales_count = query_scalar("SELECT COUNT(*) FROM FactSales WHERE ProductKey = ?", (product_key,)) or 0
    if sales_count > 0:
        return False, f"Cannot delete '{prod[0]['ProductName']}': It is referenced by {sales_count} sales transactions in FactSales."

    execute_commit("DELETE FROM DimProduct WHERE ProductKey = ?", (product_key,))
    log_activity(username, "Delete Product", "DimProduct", str(product_key), f"Deleted product SKU {prod[0]['ProductID']}.")
    return True, f"Product {prod[0]['ProductName']} deleted successfully."

# ============================================================================
# 5. STAGING AREA & ETL BATCH MANAGEMENT
# ============================================================================

def get_staging_records_admin(status=None, batch_id=None, page=1, per_page=20):
    """Retrieves records from StagingTransactions."""
    where_parts = ["1=1"]
    params = []

    if status and status.lower() != 'all':
        where_parts.append("ValidationStatus = ?")
        params.append(status)

    if batch_id and batch_id.lower() != 'all':
        where_parts.append("BatchID = ?")
        params.append(batch_id)

    where_sql = " AND ".join(where_parts)

    count_sql = f"SELECT COUNT(*) FROM StagingTransactions WHERE {where_sql}"
    total_count = query_scalar(count_sql, params if params else None) or 0

    page = max(1, int(page))
    offset = (page - 1) * per_page
    total_pages = max(1, math.ceil(total_count / per_page))

    sql = f"""
        SELECT StagingID, BatchID, InvoiceNo, InvoiceDate, CustomerID, ProductID, ProductName,
               Category, Quantity, UnitPrice, Country, ValidationStatus, ErrorMessage, ImportedAt
        FROM StagingTransactions
        WHERE {where_sql}
        ORDER BY ImportedAt DESC, StagingID DESC
        LIMIT ? OFFSET ?
    """
    list_params = list(params) + [per_page, offset]
    records = query_rows(sql, list_params)

    # Get distinct batch IDs for filter
    batches = query_rows("SELECT DISTINCT BatchID FROM StagingTransactions ORDER BY ImportedAt DESC")

    return {
        "records": records,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "batches": [b['BatchID'] for b in batches]
    }

def approve_staging_record(staging_id, username='admin'):
    """
    Manually approves a staging record:
    Ensures dimensions exist and inserts into FactSales, then updates status to 'Approved'.
    """
    row = query_rows("SELECT * FROM StagingTransactions WHERE StagingID = ?", (staging_id,))
    if not row:
        return False, "Staging record not found."

    r = row[0]
    try:
        qty = int(float(r['Quantity'] or 1))
        unit_price = float(r['UnitPrice'] or 0)
        if qty <= 0 or unit_price <= 0:
            return False, "Cannot approve: Quantity and UnitPrice must be positive numbers."

        total_amount = round(qty * unit_price, 2)
        invoice_no = str(r['InvoiceNo'] or f"MANUAL_{staging_id}")
        cust_id = str(r['CustomerID'] or "GUEST")
        prod_id = str(r['ProductID'] or "PROD_UNKNOWN")
        prod_name = str(r['ProductName'] or "Generic Item")
        cat = str(r['Category'] or "General")
        country = str(r['Country'] or "India")
        inv_date = str(r['InvoiceDate'] or datetime.date.today().strftime('%Y-%m-%d'))

        # DateKey
        date_key = int(inv_date.replace('-', '').replace('/', '')[:8])

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 1. Upsert DimCustomer
            cursor.execute("SELECT CustomerKey FROM DimCustomer WHERE CustomerID = ?", (cust_id,))
            c_row = cursor.fetchone()
            if c_row:
                cust_key = c_row[0]
            else:
                cursor.execute("""
                    INSERT INTO DimCustomer (CustomerID, CustomerName, Country, Segment, FirstPurchaseDate)
                    VALUES (?, ?, ?, 'Standard', ?)
                """, (cust_id, f"Customer {cust_id}", country, inv_date))
                cust_key = cursor.lastrowid

            # 2. Upsert DimProduct
            cursor.execute("SELECT ProductKey FROM DimProduct WHERE ProductID = ?", (prod_id,))
            p_row = cursor.fetchone()
            if p_row:
                prod_key = p_row[0]
            else:
                cursor.execute("""
                    INSERT INTO DimProduct (ProductID, ProductName, Category, UnitPrice)
                    VALUES (?, ?, ?, ?)
                """, (prod_id, prod_name, cat, unit_price))
                prod_key = cursor.lastrowid

            # 3. Upsert DimDate
            cursor.execute("SELECT DateKey FROM DimDate WHERE DateKey = ?", (date_key,))
            if not cursor.fetchone():
                dt = datetime.datetime.strptime(inv_date[:10], '%Y-%m-%d') if '-' in inv_date else datetime.datetime.now()
                cursor.execute("""
                    INSERT OR IGNORE INTO DimDate (DateKey, FullDate, Day, Month, MonthName, Quarter, Year, DayOfWeek, DayName, IsWeekend)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    date_key, dt.strftime('%Y-%m-%d'), dt.day, dt.month, dt.strftime('%B'),
                    (dt.month - 1) // 3 + 1, dt.year, dt.weekday() + 1, dt.strftime('%A'),
                    1 if dt.weekday() in [5, 6] else 0
                ))

            # 4. Upsert DimOrder
            cursor.execute("SELECT OrderKey FROM DimOrder WHERE InvoiceNo = ?", (invoice_no,))
            o_row = cursor.fetchone()
            if o_row:
                order_key = o_row[0]
                cursor.execute("""
                    UPDATE DimOrder 
                    SET TotalItems = TotalItems + ?, TotalOrderValue = TotalOrderValue + ?
                    WHERE OrderKey = ?
                """, (qty, total_amount, order_key))
            else:
                cursor.execute("""
                    INSERT INTO DimOrder (InvoiceNo, OrderDate, TotalItems, TotalOrderValue, OrderStatus)
                    VALUES (?, ?, ?, ?, 'Completed')
                """, (invoice_no, inv_date, qty, total_amount))
                order_key = cursor.lastrowid

            # 5. Insert FactSales
            cursor.execute("""
                INSERT INTO FactSales (DateKey, CustomerKey, ProductKey, OrderKey, Quantity, UnitPrice, DiscountAmount, TotalAmount, ProfitMargin)
                VALUES (?, ?, ?, ?, ?, ?, 0.0, ?, 0.25)
            """, (date_key, cust_key, prod_key, order_key, qty, unit_price, total_amount))

            # 6. Update Staging status
            cursor.execute("""
                UPDATE StagingTransactions
                SET ValidationStatus = 'Approved', ErrorMessage = 'Manually approved and loaded into warehouse.'
                WHERE StagingID = ?
            """, (staging_id,))

            conn.commit()
        finally:
            conn.close()

        log_activity(username, "Approve Staging Record", "StagingTransactions", str(staging_id), f"Approved row #{staging_id} (Invoice {invoice_no}, ₹{total_amount:.2f}) into Star Schema.")
        return True, f"Record #{staging_id} successfully loaded into data warehouse."

    except Exception as e:
        return False, f"Failed to approve record: {str(e)}"

def reject_staging_record(staging_id, reason="Manually rejected by administrator", username='admin'):
    """Marks a staging record as rejected."""
    row = query_rows("SELECT ValidationStatus FROM StagingTransactions WHERE StagingID = ?", (staging_id,))
    if not row:
        return False, "Staging record not found."

    execute_commit("""
        UPDATE StagingTransactions
        SET ValidationStatus = 'Rejected', ErrorMessage = ?
        WHERE StagingID = ?
    """, (reason, staging_id))

    log_activity(username, "Reject Staging Record", "StagingTransactions", str(staging_id), f"Rejected record #{staging_id}: {reason}")
    return True, f"Record #{staging_id} marked as Rejected."

def clear_staging_records(status=None, username='admin'):
    """Cleans up staging records."""
    if status and status.lower() != 'all':
        count = query_scalar("SELECT COUNT(*) FROM StagingTransactions WHERE ValidationStatus = ?", (status,))
        execute_commit("DELETE FROM StagingTransactions WHERE ValidationStatus = ?", (status,))
        msg = f"Cleared {count} staging records with status '{status}'."
    else:
        count = query_scalar("SELECT COUNT(*) FROM StagingTransactions")
        execute_commit("DELETE FROM StagingTransactions")
        msg = f"Cleared all {count} staging records."

    log_activity(username, "Clear Staging", "StagingTransactions", "", msg)
    return True, msg

# ============================================================================
# 6. FEEDBACK & INQUIRIES MANAGEMENT
# ============================================================================

def get_feedbacks_admin(status=None, rating=None, search=None, page=1, per_page=15):
    """Retrieves viva feedback and user submissions."""
    where_parts = ["1=1"]
    params = []

    if search:
        where_parts.append("(Name LIKE ? OR Email LIKE ? OR Subject LIKE ? OR Message LIKE ?)")
        s = f"%{search.strip()}%"
        params.extend([s, s, s, s])

    if status and status.lower() != 'all':
        where_parts.append("Status = ?")
        params.append(status)

    if rating and rating.lower() != 'all':
        where_parts.append("Rating = ?")
        params.append(int(rating))

    where_sql = " AND ".join(where_parts)

    count_sql = f"SELECT COUNT(*) FROM FeedbackSubmissions WHERE {where_sql}"
    total_count = query_scalar(count_sql, params if params else None) or 0

    page = max(1, int(page))
    offset = (page - 1) * per_page
    total_pages = max(1, math.ceil(total_count / per_page))

    sql = f"""
        SELECT FeedbackID, Name, Email, Category, Subject, Message, Rating, Status, SubmittedAt
        FROM FeedbackSubmissions
        WHERE {where_sql}
        ORDER BY SubmittedAt DESC, FeedbackID DESC
        LIMIT ? OFFSET ?
    """
    list_params = list(params) + [per_page, offset]
    feedbacks = query_rows(sql, list_params)

    return {
        "feedbacks": feedbacks,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }

def update_feedback_status(feedback_id, new_status, username='admin'):
    """Updates feedback status (e.g. New, Reviewed, Archived)."""
    valid_statuses = ['New', 'Reviewed', 'Archived']
    if new_status not in valid_statuses:
        return False, f"Invalid status '{new_status}'. Allowed: {', '.join(valid_statuses)}."

    fb = query_rows("SELECT Name, Subject FROM FeedbackSubmissions WHERE FeedbackID = ?", (feedback_id,))
    if not fb:
        return False, "Feedback submission not found."

    execute_commit("UPDATE FeedbackSubmissions SET Status = ? WHERE FeedbackID = ?", (new_status, feedback_id))
    log_activity(username, "Update Feedback Status", "FeedbackSubmissions", str(feedback_id), f"Marked feedback from '{fb[0]['Name']}' as '{new_status}'.")
    return True, f"Feedback marked as {new_status}."

def delete_feedback(feedback_id, username='admin'):
    """Deletes a feedback submission."""
    fb = query_rows("SELECT Name FROM FeedbackSubmissions WHERE FeedbackID = ?", (feedback_id,))
    if not fb:
        return False, "Feedback submission not found."

    execute_commit("DELETE FROM FeedbackSubmissions WHERE FeedbackID = ?", (feedback_id,))
    log_activity(username, "Delete Feedback", "FeedbackSubmissions", str(feedback_id), f"Deleted submission from '{fb[0]['Name']}'.")
    return True, "Feedback entry deleted successfully."

# ============================================================================
# 7. SYSTEM SETTINGS
# ============================================================================

DEFAULT_SETTINGS = {
    'currency_symbol': '₹',
    'currency_code': 'INR',
    'auto_sync_etl': 'true',
    'maintenance_mode': 'false',
    'session_timeout_minutes': '60',
    'max_upload_size_mb': '16',
    'default_min_support': '0.02',
    'default_min_confidence': '0.25',
    'default_kmeans_clusters': '4'
}

def get_system_settings():
    """Retrieves all configuration key-value settings."""
    rows = query_rows("SELECT SettingKey, SettingValue, Description, UpdatedAt FROM SystemSettings")
    settings = dict(DEFAULT_SETTINGS)
    for r in rows:
        settings[r['SettingKey']] = r['SettingValue']
    return settings

def update_system_setting(key, value, username='admin'):
    """Updates a system setting."""
    key = key.strip()
    value = str(value).strip()
    execute_commit("""
        INSERT INTO SystemSettings (SettingKey, SettingValue, UpdatedAt)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(SettingKey) DO UPDATE SET SettingValue = excluded.SettingValue, UpdatedAt = CURRENT_TIMESTAMP
    """, (key, value))
    log_activity(username, "Update Setting", "SystemSettings", key, f"Updated '{key}' to '{value}'.")
    return True, f"Setting '{key}' updated successfully."

# ============================================================================
# 8. ADMIN COCKPIT / DASHBOARD METRICS
# ============================================================================

def get_admin_dashboard_metrics():
    """Compiles consolidated operational and business metrics for the admin cockpit."""
    # Warehouse counts
    user_count = query_scalar("SELECT COUNT(*) FROM Users") or 0
    active_users = query_scalar("SELECT COUNT(*) FROM Users WHERE Status = 'Active'") or 0
    total_orders = query_scalar("SELECT COUNT(*) FROM DimOrder") or 0
    completed_orders = query_scalar("SELECT COUNT(*) FROM DimOrder WHERE OrderStatus = 'Completed'") or 0
    total_products = query_scalar("SELECT COUNT(*) FROM DimProduct") or 0
    total_customers = query_scalar("SELECT COUNT(*) FROM DimCustomer") or 0
    total_facts = query_scalar("SELECT COUNT(*) FROM FactSales") or 0
    total_revenue = query_scalar("SELECT COALESCE(SUM(TotalAmount), 0.0) FROM FactSales") or 0.0
    pending_feedback = query_scalar("SELECT COUNT(*) FROM FeedbackSubmissions WHERE Status = 'New'") or 0
    total_feedback = query_scalar("SELECT COUNT(*) FROM FeedbackSubmissions") or 0
    staging_pending = query_scalar("SELECT COUNT(*) FROM StagingTransactions WHERE ValidationStatus = 'Pending'") or 0
    staging_rejected = query_scalar("SELECT COUNT(*) FROM StagingTransactions WHERE ValidationStatus = 'Rejected'") or 0
    total_etl_batches = query_scalar("SELECT COUNT(*) FROM ETLHistory") or 0

    # Recent activity logs (top 8)
    recent_activity = get_activity_logs(limit=8)

    # Order status distribution
    order_status_rows = query_rows("""
        SELECT OrderStatus, COUNT(*) as Count, ROUND(SUM(TotalOrderValue), 2) as Value
        FROM DimOrder
        GROUP BY OrderStatus
    """)

    # User role distribution
    user_roles = query_rows("""
        SELECT Role, COUNT(*) as Count
        FROM Users
        GROUP BY Role
    """)

    return {
        "user_count": user_count,
        "active_users": active_users,
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "total_products": total_products,
        "total_customers": total_customers,
        "total_facts": total_facts,
        "total_revenue": round(float(total_revenue), 2),
        "pending_feedback": pending_feedback,
        "total_feedback": total_feedback,
        "staging_pending": staging_pending,
        "staging_rejected": staging_rejected,
        "total_etl_batches": total_etl_batches,
        "recent_activity": recent_activity,
        "order_status_distribution": order_status_rows,
        "user_roles": user_roles
    }
