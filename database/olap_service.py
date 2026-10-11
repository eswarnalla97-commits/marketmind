import pandas as pd
from database.db_manager import query_rows, query_df, get_db_connection

def get_olap_rollup(hierarchy='monthly', year=None):
    """
    OLAP Roll-up: Aggregating fine granular data into coarser dimensional hierarchies.
    Levels: 'daily' -> 'monthly' -> 'quarterly' -> 'yearly'
    """
    where_clauses = ["1=1"]
    params = []
    if year:
        where_clauses.append("d.Year = ?")
        params.append(int(year))
    
    where_str = " AND ".join(where_clauses)

    if hierarchy == 'yearly':
        sql = f"""
            SELECT 
                d.Year AS Period,
                COUNT(DISTINCT f.OrderKey) AS TotalOrders,
                SUM(f.Quantity) AS UnitsSold,
                ROUND(SUM(f.TotalAmount), 2) AS Revenue,
                ROUND(AVG(f.TotalAmount), 2) AS AvgLineItemValue
            FROM FactSales f
            JOIN DimDate d ON f.DateKey = d.DateKey
            WHERE {where_str}
            GROUP BY d.Year
            ORDER BY d.Year ASC
        """
    elif hierarchy == 'quarterly':
        sql = f"""
            SELECT 
                (d.Year || ' Q' || d.Quarter) AS Period,
                d.Year,
                ('Q' || d.Quarter) AS Quarter,
                COUNT(DISTINCT f.OrderKey) AS TotalOrders,
                SUM(f.Quantity) AS UnitsSold,
                ROUND(SUM(f.TotalAmount), 2) AS Revenue,
                ROUND(AVG(f.TotalAmount), 2) AS AvgLineItemValue
            FROM FactSales f
            JOIN DimDate d ON f.DateKey = d.DateKey
            WHERE {where_str}
            GROUP BY d.Year, d.Quarter
            ORDER BY d.Year ASC, d.Quarter ASC
        """
    elif hierarchy == 'daily':
        sql = f"""
            SELECT 
                d.FullDate AS Period,
                d.DayName,
                COUNT(DISTINCT f.OrderKey) AS TotalOrders,
                SUM(f.Quantity) AS UnitsSold,
                ROUND(SUM(f.TotalAmount), 2) AS Revenue,
                ROUND(AVG(f.TotalAmount), 2) AS AvgLineItemValue
            FROM FactSales f
            JOIN DimDate d ON f.DateKey = d.DateKey
            WHERE {where_str}
            GROUP BY d.FullDate, d.DayName
            ORDER BY d.FullDate ASC
            LIMIT 60
        """
    else:  # default monthly
        sql = f"""
            SELECT 
                (d.Year || '-' || PRINTF('%02d', d.Month)) AS Period,
                d.MonthName,
                d.Year,
                COUNT(DISTINCT f.OrderKey) AS TotalOrders,
                SUM(f.Quantity) AS UnitsSold,
                ROUND(SUM(f.TotalAmount), 2) AS Revenue,
                ROUND(AVG(f.TotalAmount), 2) AS AvgLineItemValue
            FROM FactSales f
            JOIN DimDate d ON f.DateKey = d.DateKey
            WHERE {where_str}
            GROUP BY d.Year, d.Month, d.MonthName
            ORDER BY d.Year ASC, d.Month ASC
        """

    rows = query_rows(sql, params if params else None)
    return {
        "operation": "Roll-up",
        "hierarchy": hierarchy,
        "year": year,
        "sql_query": sql.strip(),
        "rows": rows
    }

def get_olap_drilldown(dimension='category_to_product', filter_value=None):
    """
    OLAP Drill-down: De-aggregating summary data into finer granular dimensions.
    Examples:
    - 'category_to_product': Category summary -> Drill down into individual products of a category
    - 'year_to_quarter': Year summary -> Drill down into quarters of that year
    - 'quarter_to_month': Quarter summary -> Drill down into months of that quarter
    """
    params = []
    if dimension == 'category_to_product':
        if not filter_value:
            filter_value = 'Electronics'
        sql = """
            SELECT 
                p.ProductName AS ItemName,
                p.Category,
                p.ProductID,
                COUNT(DISTINCT f.OrderKey) AS TotalOrders,
                SUM(f.Quantity) AS UnitsSold,
                ROUND(SUM(f.TotalAmount), 2) AS Revenue,
                ROUND(AVG(f.UnitPrice), 2) AS AvgUnitPrice
            FROM FactSales f
            JOIN DimProduct p ON f.ProductKey = p.ProductKey
            WHERE p.Category = ?
            GROUP BY p.ProductID, p.ProductName, p.Category
            ORDER BY Revenue DESC
        """
        params.append(filter_value)
    elif dimension == 'year_to_quarter':
        year = int(filter_value) if filter_value else 2024
        sql = """
            SELECT 
                ('Q' || d.Quarter) AS ItemName,
                COUNT(DISTINCT f.OrderKey) AS TotalOrders,
                SUM(f.Quantity) AS UnitsSold,
                ROUND(SUM(f.TotalAmount), 2) AS Revenue,
                ROUND(AVG(f.TotalAmount), 2) AS AvgLineItemValue
            FROM FactSales f
            JOIN DimDate d ON f.DateKey = d.DateKey
            WHERE d.Year = ?
            GROUP BY d.Quarter
            ORDER BY d.Quarter ASC
        """
        params.append(year)
    else: # quarter_to_month
        quarter = int(filter_value) if filter_value else 1
        sql = """
            SELECT 
                d.MonthName AS ItemName,
                d.Month,
                COUNT(DISTINCT f.OrderKey) AS TotalOrders,
                SUM(f.Quantity) AS UnitsSold,
                ROUND(SUM(f.TotalAmount), 2) AS Revenue,
                ROUND(AVG(f.TotalAmount), 2) AS AvgLineItemValue
            FROM FactSales f
            JOIN DimDate d ON f.DateKey = d.DateKey
            WHERE d.Quarter = ?
            GROUP BY d.Month, d.MonthName
            ORDER BY d.Month ASC
        """
        params.append(quarter)

    rows = query_rows(sql, params)
    return {
        "operation": "Drill-down",
        "dimension": dimension,
        "filter_value": filter_value,
        "sql_query": sql.strip(),
        "rows": rows
    }

def get_olap_slice(slice_type='category', slice_value='Electronics'):
    """
    OLAP Slice: Isolates a 2D sub-plane by fixing ONE dimension to a specific single value.
    """
    params = [slice_value]
    if slice_type == 'category':
        sql = """
            SELECT 
                (d.Year || '-' || PRINTF('%02d', d.Month)) AS Period,
                d.MonthName,
                COUNT(DISTINCT f.OrderKey) AS TotalOrders,
                SUM(f.Quantity) AS UnitsSold,
                ROUND(SUM(f.TotalAmount), 2) AS Revenue
            FROM FactSales f
            JOIN DimDate d ON f.DateKey = d.DateKey
            JOIN DimProduct p ON f.ProductKey = p.ProductKey
            WHERE p.Category = ?
            GROUP BY d.Year, d.Month, d.MonthName
            ORDER BY d.Year ASC, d.Month ASC
        """
    elif slice_type == 'country':
        sql = """
            SELECT 
                p.Category AS DimensionItem,
                COUNT(DISTINCT f.OrderKey) AS TotalOrders,
                SUM(f.Quantity) AS UnitsSold,
                ROUND(SUM(f.TotalAmount), 2) AS Revenue
            FROM FactSales f
            JOIN DimCustomer c ON f.CustomerKey = c.CustomerKey
            JOIN DimProduct p ON f.ProductKey = p.ProductKey
            WHERE c.Country = ?
            GROUP BY p.Category
            ORDER BY Revenue DESC
        """
    else: # year slice
        sql = """
            SELECT 
                p.Category AS DimensionItem,
                COUNT(DISTINCT f.OrderKey) AS TotalOrders,
                SUM(f.Quantity) AS UnitsSold,
                ROUND(SUM(f.TotalAmount), 2) AS Revenue
            FROM FactSales f
            JOIN DimDate d ON f.DateKey = d.DateKey
            JOIN DimProduct p ON f.ProductKey = p.ProductKey
            WHERE d.Year = ?
            GROUP BY p.Category
            ORDER BY Revenue DESC
        """
        params = [int(slice_value) if str(slice_value).isdigit() else 2024]

    rows = query_rows(sql, params)
    return {
        "operation": "Slice",
        "slice_type": slice_type,
        "slice_value": slice_value,
        "sql_query": sql.strip(),
        "rows": rows
    }

def get_olap_dice(categories=None, countries=None, quarters=None):
    """
    OLAP Dice: Extracts a multi-dimensional sub-cube by specifying ranges/subsets on MULTIPLE dimensions.
    """
    where_parts = ["1=1"]
    params = []

    if categories and len(categories) > 0 and 'all' not in [c.lower() for c in categories]:
        placeholders = ', '.join(['?'] * len(categories))
        where_parts.append(f"p.Category IN ({placeholders})")
        params.extend(categories)

    if countries and len(countries) > 0 and 'all' not in [c.lower() for c in countries]:
        placeholders = ', '.join(['?'] * len(countries))
        where_parts.append(f"c.Country IN ({placeholders})")
        params.extend(countries)

    if quarters and len(quarters) > 0 and 'all' not in [str(q).lower() for q in quarters]:
        int_quarters = [int(q) for q in quarters if str(q).isdigit()]
        if int_quarters:
            placeholders = ', '.join(['?'] * len(int_quarters))
            where_parts.append(f"d.Quarter IN ({placeholders})")
            params.extend(int_quarters)

    where_sql = " AND ".join(where_parts)

    sql = f"""
        SELECT 
            p.Category,
            c.Country,
            ('Q' || d.Quarter) AS Quarter,
            COUNT(DISTINCT f.OrderKey) AS TotalOrders,
            SUM(f.Quantity) AS UnitsSold,
            ROUND(SUM(f.TotalAmount), 2) AS Revenue
        FROM FactSales f
        JOIN DimDate d ON f.DateKey = d.DateKey
        JOIN DimProduct p ON f.ProductKey = p.ProductKey
        JOIN DimCustomer c ON f.CustomerKey = c.CustomerKey
        WHERE {where_sql}
        GROUP BY p.Category, c.Country, d.Quarter
        ORDER BY Revenue DESC
        LIMIT 50
    """

    rows = query_rows(sql, params if params else None)
    return {
        "operation": "Dice",
        "categories": categories,
        "countries": countries,
        "quarters": quarters,
        "sql_query": sql.strip(),
        "rows": rows
    }

def get_olap_pivot(row_dim='Category', col_dim='Quarter'):
    """
    OLAP Pivot: Cross-tabulation rotation of multidimensional data.
    Generates a matrix of Category x Quarter or Country x Category.
    """
    query = """
        SELECT 
            p.Category,
            ('Q' || d.Quarter) AS Quarter,
            ROUND(SUM(f.TotalAmount), 2) AS Revenue
        FROM FactSales f
        JOIN DimDate d ON f.DateKey = d.DateKey
        JOIN DimProduct p ON f.ProductKey = p.ProductKey
        GROUP BY p.Category, d.Quarter
    """
    df = query_df(query)
    if df.empty:
        return {"rows": [], "columns": [], "matrix": []}

    pivot_df = df.pivot(index='Category', columns='Quarter', values='Revenue').fillna(0)
    pivot_df['Total'] = pivot_df.sum(axis=1)

    columns = ['Category'] + list(pivot_df.columns)
    matrix_rows = []
    for cat, r in pivot_df.iterrows():
        row_dict = {"Category": cat}
        for col in pivot_df.columns:
            row_dict[str(col)] = round(float(r[col]), 2)
        matrix_rows.append(row_dict)

    return {
        "operation": "Pivot",
        "row_dimension": row_dim,
        "col_dimension": col_dim,
        "columns": columns,
        "rows": matrix_rows
    }
