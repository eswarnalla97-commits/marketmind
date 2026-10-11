import os
import io
import csv
from flask import Blueprint, request, jsonify, send_file, current_app, Response
from werkzeug.utils import secure_filename
from config import config
from database.db_manager import get_warehouse_stats, execute_commit, query_rows, query_df
from database.analytics_service import (
    get_dashboard_kpis, get_monthly_revenue_trend, get_sales_by_category,
    get_top_selling_products, get_sales_by_country, get_available_filter_options,
    get_automated_insights
)
from database.olap_service import (
    get_olap_rollup, get_olap_drilldown, get_olap_slice, get_olap_dice, get_olap_pivot
)
from etl.etl_pipeline import validate_csv, run_etl, get_etl_history, get_staging_errors
from mining.apriori_miner import run_apriori_mining
from mining.kmeans_segmenter import run_customer_segmentation

api_bp = Blueprint('api', __name__, url_prefix='/api')

# ============================================================================
# 1. DASHBOARD & ANALYTICS APIS
# ============================================================================

@api_bp.route('/kpis', methods=['GET'])
def api_kpis():
    category = request.args.get('category')
    year = request.args.get('year')
    kpis = get_dashboard_kpis(category=category, year=year)
    return jsonify({"success": True, "data": kpis})

@api_bp.route('/monthly-revenue', methods=['GET'])
def api_monthly_revenue():
    category = request.args.get('category')
    year = request.args.get('year')
    data = get_monthly_revenue_trend(category=category, year=year)
    return jsonify({"success": True, "data": data})

@api_bp.route('/sales-by-category', methods=['GET'])
def api_sales_by_category():
    year = request.args.get('year')
    data = get_sales_by_category(year=year)
    return jsonify({"success": True, "data": data})

@api_bp.route('/sales-by-country', methods=['GET'])
def api_sales_by_country():
    data = get_sales_by_country()
    return jsonify({"success": True, "data": data})

@api_bp.route('/top-products', methods=['GET'])
def api_top_products():
    limit = int(request.args.get('limit', 10))
    category = request.args.get('category')
    data = get_top_selling_products(limit=limit, category=category)
    return jsonify({"success": True, "data": data})

@api_bp.route('/filter-options', methods=['GET'])
def api_filter_options():
    options = get_available_filter_options()
    return jsonify({"success": True, "data": options})

@api_bp.route('/warehouse-stats', methods=['GET'])
def api_warehouse_stats():
    stats = get_warehouse_stats()
    return jsonify({"success": True, "data": stats})

# ============================================================================
# 2. DATA MINING APIS (APRIORI & K-MEANS)
# ============================================================================

@api_bp.route('/apriori', methods=['GET', 'POST'])
def api_apriori():
    if request.method == 'POST':
        req_data = request.get_json(silent=True) or request.form
        min_support = float(req_data.get('min_support', 0.02))
        min_confidence = float(req_data.get('min_confidence', 0.25))
        sort_by = req_data.get('sort_by', 'lift')
        category = req_data.get('category', None)
    else:
        min_support = float(request.args.get('min_support', 0.02))
        min_confidence = float(request.args.get('min_confidence', 0.25))
        sort_by = request.args.get('sort_by', 'lift')
        category = request.args.get('category', None)

    result = run_apriori_mining(
        min_support=min_support,
        min_confidence=min_confidence,
        sort_by=sort_by,
        category=category
    )
    return jsonify(result)

@api_bp.route('/kmeans', methods=['GET', 'POST'])
def api_kmeans():
    if request.method == 'POST':
        req_data = request.get_json(silent=True) or request.form
        k = int(req_data.get('k_clusters', 4))
    else:
        k = int(request.args.get('k_clusters', 4))

    result = run_customer_segmentation(k_clusters=k)
    return jsonify(result)

# ============================================================================
# 3. OLAP OPERATIONS APIS
# ============================================================================

@api_bp.route('/olap/rollup', methods=['GET'])
def api_olap_rollup():
    hierarchy = request.args.get('hierarchy', 'monthly')
    year = request.args.get('year', None)
    result = get_olap_rollup(hierarchy=hierarchy, year=year)
    return jsonify({"success": True, "data": result})

@api_bp.route('/olap/drilldown', methods=['GET'])
def api_olap_drilldown():
    dim = request.args.get('dimension', 'category_to_product')
    val = request.args.get('filter_value', None)
    result = get_olap_drilldown(dimension=dim, filter_value=val)
    return jsonify({"success": True, "data": result})

@api_bp.route('/olap/slice', methods=['GET'])
def api_olap_slice():
    slice_type = request.args.get('slice_type', 'category')
    slice_val = request.args.get('slice_value', 'Electronics')
    result = get_olap_slice(slice_type=slice_type, slice_value=slice_val)
    return jsonify({"success": True, "data": result})

@api_bp.route('/olap/dice', methods=['POST'])
def api_olap_dice():
    data = request.get_json(silent=True) or {}
    cats = data.get('categories', [])
    countries = data.get('countries', [])
    quarters = data.get('quarters', [])
    result = get_olap_dice(categories=cats, countries=countries, quarters=quarters)
    return jsonify({"success": True, "data": result})

@api_bp.route('/olap/pivot', methods=['GET'])
def api_olap_pivot():
    row_dim = request.args.get('row_dim', 'Category')
    col_dim = request.args.get('col_dim', 'Quarter')
    result = get_olap_pivot(row_dim=row_dim, col_dim=col_dim)
    return jsonify({"success": True, "data": result})

# ============================================================================
# 4. ETL & DATA IMPORT APIS
# ============================================================================

@api_bp.route('/upload-csv', methods=['POST'])
def api_upload_csv():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded."}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"success": False, "message": "No file selected."}), 400

    filename = secure_filename(file.filename)
    if not filename.lower().endswith('.csv'):
        return jsonify({"success": False, "message": "Only CSV files are supported."}), 400

    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    temp_path = os.path.join(config.UPLOAD_FOLDER, filename)
    file.save(temp_path)

    # Validate structure
    is_valid, msg, info = validate_csv(temp_path)
    if not is_valid:
        return jsonify({
            "success": False,
            "message": msg,
            "info": info,
            "file_path": temp_path,
            "filename": filename
        }), 400

    return jsonify({
        "success": True,
        "message": msg,
        "filename": filename,
        "file_path": temp_path,
        "info": info
    })

@api_bp.route('/run-etl', methods=['POST'])
def api_run_etl():
    data = request.get_json(silent=True) or {}
    file_path = data.get('file_path')
    filename = data.get('filename', 'uploaded_transactions.csv')

    if not file_path or not os.path.exists(file_path):
        # Fall back to sample transactions if none specified
        file_path = config.SAMPLE_DATA_PATH
        filename = "sample_transactions.csv"

    result = run_etl(file_path, original_filename=filename)
    return jsonify(result)

@api_bp.route('/etl-history', methods=['GET'])
def api_etl_history():
    history = get_etl_history(limit=20)
    return jsonify({"success": True, "data": history})

@api_bp.route('/staging-errors', methods=['GET'])
def api_staging_errors():
    batch_id = request.args.get('batch_id')
    errors = get_staging_errors(batch_id=batch_id, limit=50)
    return jsonify({"success": True, "data": errors})

@api_bp.route('/download-template', methods=['GET'])
def api_download_template():
    if not os.path.exists(config.SAMPLE_TEMPLATE_PATH):
        return jsonify({"error": "Template file not found"}), 404
    return send_file(
        config.SAMPLE_TEMPLATE_PATH,
        as_attachment=True,
        download_name="marketmind_transaction_template.csv",
        mimetype="text/csv"
    )

@api_bp.route('/download-sample-data', methods=['GET'])
def api_download_sample_data():
    if not os.path.exists(config.SAMPLE_DATA_PATH):
        return jsonify({"error": "Sample data file not found"}), 404
    return send_file(
        config.SAMPLE_DATA_PATH,
        as_attachment=True,
        download_name="marketmind_sample_transactions.csv",
        mimetype="text/csv"
    )

# ============================================================================
# 5. REPORTS & CSV EXPORTS
# ============================================================================

@api_bp.route('/export-report/<report_type>', methods=['GET'])
def api_export_report(report_type):
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'sales':
        rows = get_monthly_revenue_trend()
        writer.writerow(['Period', 'Month', 'Year', 'Revenue (₹)', 'Orders Count', 'Units Sold'])
        for r in rows:
            writer.writerow([r['Period'], r['MonthName'], r['Year'], r['Revenue'], r['Orders'], r['Units']])
        filename = "marketmind_sales_performance.csv"

    elif report_type == 'products':
        rows = get_top_selling_products(limit=100)
        writer.writerow(['ProductID', 'ProductName', 'Category', 'UnitPrice (₹)', 'UnitsSold', 'TotalRevenue (₹)', 'OrdersCount'])
        for r in rows:
            writer.writerow([r['ProductID'], r['ProductName'], r['Category'], r['UnitPrice'], r['UnitsSold'], r['TotalRevenue'], r['OrdersCount']])
        filename = "marketmind_product_performance.csv"

    elif report_type == 'segments':
        seg_data = run_customer_segmentation(k_clusters=4)
        writer.writerow(['CustomerID', 'State / Region', 'TotalSpend (₹)', 'OrdersCount', 'AvgOrderValue (₹)', 'RecencyDays', 'ClusterID', 'SegmentName'])
        for c in seg_data.get('customers', []):
            writer.writerow([c['customer_id'], c['country'], c['monetary'], c['frequency'], c['aov'], c['recency'], c['cluster_id'], c['segment_name']])
        filename = "marketmind_customer_segments.csv"

    elif report_type == 'associations':
        assoc_data = run_apriori_mining(min_support=0.015, min_confidence=0.20)
        writer.writerow(['RuleID', 'Antecedents', 'Consequents', 'Support (%)', 'Confidence (%)', 'Lift', 'Explanation'])
        for rule in assoc_data.get('rules', []):
            writer.writerow([rule['id'], rule['antecedents_str'], rule['consequents_str'], rule['support_pct'], rule['confidence_pct'], rule['lift'], rule['explanation']])
        filename = "marketmind_association_rules.csv"

    else:
        return jsonify({"error": "Invalid report type"}), 400

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

# ============================================================================
# 6. CONTACT & FEEDBACK APIS
# ============================================================================

@api_bp.route('/contact', methods=['POST'])
def api_contact():
    data = request.get_json(silent=True) or request.form
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    category = (data.get('category') or 'General Inquiry').strip()
    subject = (data.get('subject') or '').strip()
    message = (data.get('message') or '').strip()
    rating = int(data.get('rating') or 5)

    if not name or not email or not subject or not message:
        return jsonify({"success": False, "message": "Please fill in all required fields."}), 400

    try:
        feedback_id = execute_commit("""
            INSERT INTO FeedbackSubmissions (Name, Email, Category, Subject, Message, Rating, Status)
            VALUES (?, ?, ?, ?, ?, ?, 'New')
        """, (name, email, category, subject, message, rating))

        return jsonify({
            "success": True,
            "message": "Thank you! Your feedback has been stored in the project database.",
            "feedback_id": feedback_id
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
