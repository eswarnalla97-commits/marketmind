import os
from flask import Flask, render_template
from config import config
from database.db_manager import init_db, get_warehouse_stats, query_scalar, execute_commit
from routes.main_routes import main_bp
from routes.api_routes import api_bp
from routes.admin_routes import admin_bp
from routes.admin_api_routes import admin_api_bp
from werkzeug.security import generate_password_hash

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # Ensure required directories exist
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)

    # Initialize database if not already initialized
    if not os.path.exists(config.DATABASE_PATH):
        print("Database not found. Initializing schema...")
        init_db()

    # Ensure Admin tables and default admin account exist
    try:
        user_count = query_scalar("SELECT COUNT(*) FROM Users") or 0
        if user_count == 0:
            execute_commit("""
                INSERT INTO Users (Username, Email, PasswordHash, FullName, Role, Status)
                VALUES 
                (?, ?, ?, ?, 'Admin', 'Active'),
                (?, ?, ?, ?, 'Analyst', 'Active'),
                (?, ?, ?, ?, 'Viewer', 'Active')
            """, (
                'admin', 'admin@marketmind.internal', generate_password_hash('Admin@MarketMind2024'), 'Dr. Rajesh Sharma (Lead DWDM Admin)',
                'analyst_priya', 'priya.verma@marketmind.internal', generate_password_hash('Priya@2024'), 'Priya Verma (Data Analyst)',
                'viewer_arun', 'arun.nair@marketmind.internal', generate_password_hash('Viewer@2024'), 'Arun Nair (Executive Stakeholder)'
            ))
            from database.admin_service import DEFAULT_SETTINGS
            for k, v in DEFAULT_SETTINGS.items():
                execute_commit("INSERT OR IGNORE INTO SystemSettings (SettingKey, SettingValue) VALUES (?, ?)", (k, v))
    except Exception as e:
        pass

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_api_bp)

    # Indian Currency (INR - ₹) Formatting Filter
    def format_indian_currency(val):
        """Formats numbers into Indian numbering system: e.g. ₹12,34,567.89"""
        try:
            val = float(val)
            is_negative = val < 0
            val = abs(val)
            parts = f"{val:.2f}".split('.')
            integer_part = parts[0]
            decimal_part = parts[1]
            if len(integer_part) <= 3:
                formatted_int = integer_part
            else:
                last_three = integer_part[-3:]
                remaining = integer_part[:-3]
                groups = []
                while len(remaining) > 2:
                    groups.insert(0, remaining[-2:])
                    remaining = remaining[:-2]
                if remaining:
                    groups.insert(0, remaining)
                groups.append(last_three)
                formatted_int = ','.join(groups)
            sign = '-' if is_negative else ''
            return f"{sign}₹{formatted_int}.{decimal_part}"
        except (ValueError, TypeError):
            return "₹0.00"

    app.jinja_env.filters['inr'] = format_indian_currency

    # Global context processor for template navbar stats and branding
    @app.context_processor
    def inject_global_data():
        try:
            stats = get_warehouse_stats()
        except Exception:
            stats = {}
        from flask import session
        current_user = {
            'is_authenticated': 'user_id' in session,
            'id': session.get('user_id'),
            'username': session.get('username'),
            'role': session.get('role'),
            'full_name': session.get('full_name'),
            'email': session.get('email'),
            'avatar': session.get('avatar', 'fa-user-tie')
        }
        return {
            'app_name': 'MarketMind',
            'global_stats': stats,
            'current_year': 2024,
            'format_inr': format_indian_currency,
            'current_user': current_user
        }

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', content_error="Page not found (404)"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('base.html', content_error=f"Internal Server Error: {str(e)}"), 500

    return app

app = create_app()

if __name__ == '__main__':
    print("==================================================")
    print("MarketMind Web Portal Starting on http://127.0.0.1:5000")
    print("==================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)
