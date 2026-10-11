import pandas as pd
from database.db_manager import query_rows, query_df, query_scalar

def get_dashboard_kpis(category=None, year=None):
    """
    Computes key executive KPIs from FactSales.
    All figures are derived from actual warehouse data.
    """
    where_parts = ["1=1"]
    params = []

    if category and category.lower() != 'all':
        where_parts.append("p.Category = ?")
        params.append(category)

    if year and year.lower() != 'all':
        where_parts.append("d.Year = ?")
        params.append(int(year))

    where_sql = " AND ".join(where_parts)

    sql = f"""
        SELECT 
            COUNT(f.SalesKey) AS TotalLineItems,
            COUNT(DISTINCT f.OrderKey) AS TotalOrders,
            COUNT(DISTINCT f.CustomerKey) AS TotalCustomers,
            COALESCE(SUM(f.Quantity), 0) AS TotalProductsSold,
            COALESCE(ROUND(SUM(f.TotalAmount), 2), 0.0) AS TotalRevenue
        FROM FactSales f
        JOIN DimDate d ON f.DateKey = d.DateKey
        JOIN DimProduct p ON f.ProductKey = p.ProductKey
        WHERE {where_sql}
    """
    row = query_rows(sql, params if params else None)[0]

    total_rev = float(row['TotalRevenue'] or 0.0)
    total_orders = int(row['TotalOrders'] or 0)
    aov = round(total_rev / total_orders, 2) if total_orders > 0 else 0.0

    return {
        "total_revenue": total_rev,
        "total_orders": total_orders,
        "total_customers": int(row['TotalCustomers'] or 0),
        "total_products_sold": int(row['TotalProductsSold'] or 0),
        "average_order_value": aov,
        "total_line_items": int(row['TotalLineItems'] or 0)
    }

def get_monthly_revenue_trend(category=None, year=None):
    """Monthly revenue time series for Chart.js area/line chart."""
    where_parts = ["1=1"]
    params = []

    if category and category.lower() != 'all':
        where_parts.append("p.Category = ?")
        params.append(category)

    if year and year.lower() != 'all':
        where_parts.append("d.Year = ?")
        params.append(int(year))

    where_sql = " AND ".join(where_parts)

    sql = f"""
        SELECT 
            (d.Year || '-' || PRINTF('%02d', d.Month)) AS Period,
            d.MonthName,
            d.Year,
            ROUND(SUM(f.TotalAmount), 2) AS Revenue,
            COUNT(DISTINCT f.OrderKey) AS Orders,
            SUM(f.Quantity) AS Units
        FROM FactSales f
        JOIN DimDate d ON f.DateKey = d.DateKey
        JOIN DimProduct p ON f.ProductKey = p.ProductKey
        WHERE {where_sql}
        GROUP BY d.Year, d.Month, d.MonthName
        ORDER BY d.Year ASC, d.Month ASC
    """
    return query_rows(sql, params if params else None)

def get_sales_by_category(year=None):
    """Sales breakdown by Category for donut/pie chart."""
    where_parts = ["1=1"]
    params = []

    if year and year.lower() != 'all':
        where_parts.append("d.Year = ?")
        params.append(int(year))

    where_sql = " AND ".join(where_parts)

    sql = f"""
        SELECT 
            p.Category,
            ROUND(SUM(f.TotalAmount), 2) AS Revenue,
            SUM(f.Quantity) AS Units,
            COUNT(DISTINCT f.OrderKey) AS Orders
        FROM FactSales f
        JOIN DimProduct p ON f.ProductKey = p.ProductKey
        JOIN DimDate d ON f.DateKey = d.DateKey
        WHERE {where_sql}
        GROUP BY p.Category
        ORDER BY Revenue DESC
    """
    rows = query_rows(sql, params if params else None)
    total_rev = sum(r['Revenue'] for r in rows) if rows else 1.0

    for r in rows:
        r['Percentage'] = round((r['Revenue'] / total_rev) * 100, 1)

    return rows

def get_top_selling_products(limit=10, category=None):
    """Top selling products table."""
    where_parts = ["1=1"]
    params = []

    if category and category.lower() != 'all':
        where_parts.append("p.Category = ?")
        params.append(category)

    where_sql = " AND ".join(where_parts)

    sql = f"""
        SELECT 
            p.ProductID,
            p.ProductName,
            p.Category,
            p.UnitPrice,
            SUM(f.Quantity) AS UnitsSold,
            ROUND(SUM(f.TotalAmount), 2) AS TotalRevenue,
            COUNT(DISTINCT f.OrderKey) AS OrdersCount
        FROM FactSales f
        JOIN DimProduct p ON f.ProductKey = p.ProductKey
        WHERE {where_sql}
        GROUP BY p.ProductID, p.ProductName, p.Category, p.UnitPrice
        ORDER BY TotalRevenue DESC
        LIMIT ?
    """
    params.append(limit)
    return query_rows(sql, params)

def get_sales_by_country():
    """Sales breakdown by customer country."""
    sql = """
        SELECT 
            c.Country,
            COUNT(DISTINCT c.CustomerKey) AS CustomersCount,
            COUNT(DISTINCT f.OrderKey) AS OrdersCount,
            ROUND(SUM(f.TotalAmount), 2) AS Revenue
        FROM FactSales f
        JOIN DimCustomer c ON f.CustomerKey = c.CustomerKey
        GROUP BY c.Country
        ORDER BY Revenue DESC
    """
    return query_rows(sql)

def get_available_filter_options():
    """Retrieves unique categories and years for dropdown filters."""
    categories = query_rows("SELECT DISTINCT Category FROM DimProduct ORDER BY Category ASC")
    years = query_rows("SELECT DISTINCT Year FROM DimDate ORDER BY Year DESC")
    return {
        "categories": [c['Category'] for c in categories],
        "years": [y['Year'] for y in years]
    }

def get_automated_insights():
    """Generates intelligent data-driven business insights from warehouse metrics."""
    insights = []

    # 1. Top Category
    cat_rows = get_sales_by_category()
    if cat_rows:
        top_cat = cat_rows[0]
        insights.append({
            "type": "Revenue Driver",
            "icon": "fa-chart-pie",
            "badge": "Dominant Category",
            "badge_color": "bg-primary",
            "title": f"{top_cat['Category']} Leads Sales",
            "text": f"{top_cat['Category']} is your largest revenue engine, generating ₹{top_cat['Revenue']:,.2f} ({top_cat['Percentage']}% of total sales) across {top_cat['Units']} units sold."
        })

    # 2. Top Product
    top_prods = get_top_selling_products(limit=1)
    if top_prods:
        tp = top_prods[0]
        insights.append({
            "type": "Hero Product",
            "icon": "fa-star",
            "badge": "Top Performer",
            "badge_color": "bg-success",
            "title": f"{tp['ProductName']} is #1 Bestseller",
            "text": f"Outperformed all catalog items with ₹{tp['TotalRevenue']:,.2f} in sales across {tp['UnitsSold']} units in {tp['OrdersCount']} distinct orders."
        })

    # 3. Geographic Concentration
    geo_rows = get_sales_by_country()
    if geo_rows:
        top_country = geo_rows[0]
        total_rev = sum(g['Revenue'] for g in geo_rows)
        pct = round((top_country['Revenue'] / total_rev) * 100, 1) if total_rev > 0 else 0
        insights.append({
            "type": "Market Geography",
            "icon": "fa-globe",
            "badge": "Regional Hub",
            "badge_color": "bg-info",
            "title": f"{top_country['Country']} Generates {pct}% of Demand",
            "text": f"Customer demand is heavily concentrated in {top_country['Country']} with {top_country['CustomersCount']} active accounts generating ₹{top_country['Revenue']:,.2f}."
        })

    # 4. Seasonal Peak
    trends = get_monthly_revenue_trend()
    if trends:
        peak_month = max(trends, key=lambda x: x['Revenue'])
        insights.append({
            "type": "Temporal Seasonality",
            "icon": "fa-calendar-check",
            "badge": "Peak Velocity",
            "badge_color": "bg-warning",
            "title": f"Peak Revenue Recorded in {peak_month['MonthName']} {peak_month['Year']}",
            "text": f"Achieved monthly high revenue of ₹{peak_month['Revenue']:,.2f} across {peak_month['Orders']} orders, representing maximum sales velocity."
        })

    return insights
