from flask import Blueprint, render_template, request
from database.db_manager import get_warehouse_stats, query_rows
from database.analytics_service import get_dashboard_kpis, get_available_filter_options, get_automated_insights
from etl.etl_pipeline import get_etl_history

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Page 1: Public Home Page"""
    stats = get_warehouse_stats()
    kpis = get_dashboard_kpis()
    return render_template('index.html', stats=stats, kpis=kpis)

@main_bp.route('/about')
def about():
    """Page 2: About and Project Information"""
    stats = get_warehouse_stats()
    return render_template('about.html', stats=stats)

@main_bp.route('/dashboard')
def dashboard():
    """Page 3: Main Analytics Dashboard"""
    kpis = get_dashboard_kpis()
    filter_opts = get_available_filter_options()
    insights = get_automated_insights()
    return render_template('dashboard.html', kpis=kpis, filter_opts=filter_opts, insights=insights)

@main_bp.route('/data-import')
def data_import():
    """Page 4: Data Import and ETL Portal"""
    etl_history = get_etl_history(limit=10)
    stats = get_warehouse_stats()
    return render_template('data_import.html', etl_history=etl_history, stats=stats)

@main_bp.route('/product-mining')
def product_mining():
    """Page 5: Product Association Mining (Apriori)"""
    filter_opts = get_available_filter_options()
    return render_template('product_mining.html', filter_opts=filter_opts)

@main_bp.route('/customer-segmentation')
def customer_segmentation():
    """Page 6: Customer Segmentation (K-Means)"""
    return render_template('customer_segmentation.html')

@main_bp.route('/olap')
def olap():
    """Page 7: OLAP Analytics (Roll-up, Drill-down, Slice, Dice)"""
    filter_opts = get_available_filter_options()
    countries = query_rows("SELECT DISTINCT Country FROM DimCustomer ORDER BY Country ASC")
    country_list = [c['Country'] for c in countries]
    return render_template('olap.html', filter_opts=filter_opts, countries=country_list)

@main_bp.route('/reports')
def reports():
    """Page 8: Reports and Insights"""
    kpis = get_dashboard_kpis()
    insights = get_automated_insights()
    return render_template('reports.html', kpis=kpis, insights=insights)

@main_bp.route('/contact')
def contact():
    """Page 9: Contact and Viva Feedback"""
    feedbacks = query_rows("SELECT * FROM FeedbackSubmissions ORDER BY SubmittedAt DESC LIMIT 10")
    return render_template('contact.html', feedbacks=feedbacks)
