import os
from flask import Flask, render_template
from config import config
from database.db_manager import init_db, get_warehouse_stats
from routes.main_routes import main_bp
from routes.api_routes import api_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    # Ensure required directories exist
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)

    # Initialize database if not already initialized
    if not os.path.exists(config.DATABASE_PATH):
        print("Database not found. Initializing schema...")
        init_db()

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

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
        return {
            'app_name': 'MarketMind',
            'global_stats': stats,
            'current_year': 2024,
            'format_inr': format_indian_currency
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
