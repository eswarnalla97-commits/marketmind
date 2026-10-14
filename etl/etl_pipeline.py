import os
import time
import uuid
import datetime
import pandas as pd
import numpy as np
from database.db_manager import get_db_connection

REQUIRED_COLUMNS = [
    'InvoiceNo', 'InvoiceDate', 'CustomerID', 'ProductID', 
    'ProductName', 'Category', 'Quantity', 'UnitPrice', 'Country'
]

def validate_csv(file_path):
    """
    Validates CSV headers and basic integrity before ingestion.
    Returns: (is_valid, message, info_dict)
    """
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}", {}

    try:
        df_preview = pd.read_csv(file_path, nrows=5)
    except Exception as e:
        return False, f"Error reading CSV: {str(e)}", {}

    columns_found = [str(c).strip() for c in df_preview.columns]
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in columns_found]

    if missing_cols:
        return False, f"Missing required columns: {', '.join(missing_cols)}", {
            "columns_found": columns_found,
            "missing_columns": missing_cols,
            "required_columns": REQUIRED_COLUMNS
        }

    total_rows = 0
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            total_rows = sum(1 for _ in f) - 1
    except Exception:
        total_rows = len(df_preview)

    return True, "CSV structure is valid and ready for ETL pipeline.", {
        "columns_found": columns_found,
        "missing_columns": [],
        "required_columns": REQUIRED_COLUMNS,
        "estimated_rows": max(0, total_rows),
        "preview": df_preview.to_dict(orient='records')
    }

def run_etl(file_path, original_filename="uploaded_file.csv", batch_id=None):
    """
    Executes the complete ETL Pipeline:
    1. Extract from CSV
    2. Validate, Cleanse & Transform
    3. Load into Staging
    4. Upsert into Dimensions (DimDate, DimCustomer, DimProduct, DimOrder)
    5. Load into FactSales with surrogate keys
    6. Record ETL run in ETLHistory
    """
    start_time = time.time()
    if not batch_id:
        batch_id = f"BATCH_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4].upper()}"

    conn = get_db_connection()
    cursor = conn.cursor()

    errors = []
    total_records = 0
    accepted_records = 0
    rejected_records = 0
    duplicate_records = 0

    try:
        # Step 1: Read Raw CSV
        df = pd.read_csv(file_path, dtype={
            'InvoiceNo': str,
            'CustomerID': str,
            'ProductID': str,
            'ProductName': str,
            'Category': str,
            'Country': str
        })
        # Strip header whitespaces
        df.columns = [str(c).strip() for c in df.columns]
        total_records = len(df)

        if total_records == 0:
            raise ValueError("CSV file contains 0 data rows.")

        # Step 2: Cleanse & Validate
        # Identify Duplicates
        duplicate_mask = df.duplicated(subset=['InvoiceNo', 'CustomerID', 'ProductID'], keep='first')
        duplicate_records = int(duplicate_mask.sum())

        staging_rows = []
        valid_rows = []

        for idx, row in df.iterrows():
            is_dup = bool(duplicate_mask.iloc[idx])
            err_msg = []

            inv_no = str(row.get('InvoiceNo', '')).strip()
            inv_date = str(row.get('InvoiceDate', '')).strip()
            cust_id = str(row.get('CustomerID', '')).strip()
            prod_id = str(row.get('ProductID', '')).strip()
            prod_name = str(row.get('ProductName', '')).strip()
            category = str(row.get('Category', '')).strip()
            country = str(row.get('Country', '')).strip() or 'United States'
            raw_qty = row.get('Quantity')
            raw_price = row.get('UnitPrice')

            # Validations
            if not inv_no or inv_no.lower() == 'nan':
                err_msg.append("Missing InvoiceNo")
            if not cust_id or cust_id.lower() == 'nan':
                err_msg.append("Missing CustomerID")
            if not prod_id or prod_id.lower() == 'nan':
                err_msg.append("Missing ProductID")
            if not prod_name or prod_name.lower() == 'nan':
                prod_name = f"Product-{prod_id}" if prod_id else "Unknown Product"
            if not category or category.lower() == 'nan':
                category = "General"

            try:
                qty = int(float(raw_qty))
                if qty <= 0:
                    err_msg.append(f"Invalid Quantity ({qty})")
            except (ValueError, TypeError):
                qty = 0
                err_msg.append("Non-numeric Quantity")

            try:
                price = float(raw_price)
                if price <= 0:
                    err_msg.append(f"Invalid UnitPrice ({price})")
            except (ValueError, TypeError):
                price = 0.0
                err_msg.append("Non-numeric UnitPrice")

            # Date parsing
            parsed_date = None
            try:
                parsed_dt = pd.to_datetime(inv_date)
                parsed_date = parsed_dt.strftime('%Y-%m-%d')
            except Exception:
                err_msg.append(f"Invalid Date ({inv_date})")

            is_valid = (len(err_msg) == 0 and not is_dup)

            val_status = 'Valid'
            if is_dup:
                val_status = 'Duplicate'
                err_msg.append("Duplicate item within same invoice")
            elif not is_valid:
                val_status = 'Rejected'

            error_str = "; ".join(err_msg) if err_msg else None

            staging_rows.append((
                batch_id, inv_no, inv_date, cust_id, prod_id, prod_name,
                category, qty, price, country, val_status, error_str
            ))

            if is_valid:
                valid_rows.append({
                    'InvoiceNo': inv_no,
                    'InvoiceDate': parsed_date,
                    'CustomerID': cust_id,
                    'ProductID': prod_id,
                    'ProductName': prod_name,
                    'Category': category,
                    'Quantity': qty,
                    'UnitPrice': price,
                    'Country': country,
                    'TotalAmount': round(qty * price, 2)
                })
            else:
                rejected_records += 1

        accepted_records = len(valid_rows)

        # Bulk insert into StagingTransactions
        cursor.executemany("""
            INSERT INTO StagingTransactions (
                BatchID, InvoiceNo, InvoiceDate, CustomerID, ProductID,
                ProductName, Category, Quantity, UnitPrice, Country,
                ValidationStatus, ErrorMessage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, staging_rows)

        if accepted_records == 0:
            raise ValueError(f"All {total_records} rows were rejected due to data validation issues.")

        df_valid = pd.DataFrame(valid_rows)

        # Step 3: Populate DimDate
        unique_dates = df_valid['InvoiceDate'].drop_duplicates().tolist()
        date_records = []
        for d_str in unique_dates:
            dt = datetime.datetime.strptime(d_str, '%Y-%m-%d')
            date_key = int(dt.strftime('%Y%m%d'))
            is_weekend = 1 if dt.weekday() >= 5 else 0
            quarter = (dt.month - 1) // 3 + 1
            date_records.append((
                date_key, d_str, dt.day, dt.month, dt.strftime('%B'),
                quarter, dt.year, dt.weekday(), dt.strftime('%A'), is_weekend
            ))

        cursor.executemany("""
            INSERT OR IGNORE INTO DimDate (
                DateKey, FullDate, Day, Month, MonthName,
                Quarter, Year, DayOfWeek, DayName, IsWeekend
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, date_records)

        # Step 4: Populate DimCustomer
        cust_df = df_valid[['CustomerID', 'Country', 'InvoiceDate']].drop_duplicates(subset=['CustomerID'])
        for _, c_row in cust_df.iterrows():
            cid = c_row['CustomerID']
            cname = f"Customer {cid}"
            country = c_row['Country']
            first_date = c_row['InvoiceDate']
            cursor.execute("""
                INSERT INTO DimCustomer (CustomerID, CustomerName, Country, Segment, FirstPurchaseDate)
                VALUES (?, ?, ?, 'Standard', ?)
                ON CONFLICT(CustomerID) DO UPDATE SET
                    Country = excluded.Country
            """, (cid, cname, country, first_date))

        # Step 5: Populate DimProduct
        prod_df = df_valid[['ProductID', 'ProductName', 'Category', 'UnitPrice']].drop_duplicates(subset=['ProductID'])
        for _, p_row in prod_df.iterrows():
            pid = p_row['ProductID']
            pname = p_row['ProductName']
            cat = p_row['Category']
            uprice = p_row['UnitPrice']
            cursor.execute("""
                INSERT INTO DimProduct (ProductID, ProductName, Category, UnitPrice)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(ProductID) DO UPDATE SET
                    ProductName = excluded.ProductName,
                    Category = excluded.Category,
                    UnitPrice = excluded.UnitPrice
            """, (pid, pname, cat, uprice))

        # Step 6: Populate DimOrder
        order_agg = df_valid.groupby('InvoiceNo').agg(
            OrderDate=('InvoiceDate', 'first'),
            TotalItems=('Quantity', 'sum'),
            TotalOrderValue=('TotalAmount', 'sum')
        ).reset_index()

        for _, o_row in order_agg.iterrows():
            cursor.execute("""
                INSERT INTO DimOrder (InvoiceNo, OrderDate, TotalItems, TotalOrderValue, OrderStatus)
                VALUES (?, ?, ?, ?, 'Completed')
                ON CONFLICT(InvoiceNo) DO UPDATE SET
                    TotalItems = excluded.TotalItems,
                    TotalOrderValue = excluded.TotalOrderValue
            """, (o_row['InvoiceNo'], o_row['OrderDate'], int(o_row['TotalItems']), float(round(o_row['TotalOrderValue'], 2))))

        conn.commit()

        # Step 7: Load FactSales using surrogate keys
        # Fetch surrogate key mappings
        cursor.execute("SELECT CustomerID, CustomerKey FROM DimCustomer")
        customer_map = dict(cursor.fetchall())

        cursor.execute("SELECT ProductID, ProductKey FROM DimProduct")
        product_map = dict(cursor.fetchall())

        cursor.execute("SELECT InvoiceNo, OrderKey FROM DimOrder")
        order_map = dict(cursor.fetchall())

        cursor.execute("SELECT FullDate, DateKey FROM DimDate")
        date_map = dict(cursor.fetchall())

        fact_records = []
        for _, row in df_valid.iterrows():
            date_key = date_map.get(row['InvoiceDate'])
            customer_key = customer_map.get(row['CustomerID'])
            product_key = product_map.get(row['ProductID'])
            order_key = order_map.get(row['InvoiceNo'])

            if date_key and customer_key and product_key and order_key:
                fact_records.append((
                    date_key, customer_key, product_key, order_key,
                    int(row['Quantity']), float(row['UnitPrice']),
                    0.0, float(row['TotalAmount']), 0.25
                ))

        cursor.executemany("""
            INSERT INTO FactSales (
                DateKey, CustomerKey, ProductKey, OrderKey,
                Quantity, UnitPrice, DiscountAmount, TotalAmount, ProfitMargin
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, fact_records)

        duration = round(time.time() - start_time, 2)
        status = 'Success' if rejected_records == 0 else 'Partial'

        cursor.execute("""
            INSERT OR REPLACE INTO ETLHistory (
                BatchID, FileName, TotalRecords, AcceptedRecords,
                RejectedRecords, DuplicateRecords, ExecutionTimeSeconds,
                Status, Details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id, original_filename, total_records, accepted_records,
            rejected_records, duplicate_records, duration, status,
            f"Fact rows loaded: {len(fact_records)}"
        ))

        conn.commit()

        return {
            "success": True,
            "batch_id": batch_id,
            "file_name": original_filename,
            "total_records": total_records,
            "accepted_records": accepted_records,
            "rejected_records": rejected_records,
            "duplicate_records": duplicate_records,
            "fact_rows_inserted": len(fact_records),
            "execution_time_seconds": duration,
            "status": status,
            "message": f"Successfully processed {accepted_records} records in {duration}s."
        }

    except Exception as e:
        conn.rollback()
        duration = round(time.time() - start_time, 2)
        cursor.execute("""
            INSERT OR REPLACE INTO ETLHistory (
                BatchID, FileName, TotalRecords, AcceptedRecords,
                RejectedRecords, DuplicateRecords, ExecutionTimeSeconds,
                Status, Details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id, original_filename, total_records, accepted_records,
            rejected_records, duplicate_records, duration, 'Failed', str(e)
        ))
        conn.commit()
        return {
            "success": False,
            "batch_id": batch_id,
            "file_name": original_filename,
            "total_records": total_records,
            "accepted_records": 0,
            "rejected_records": total_records,
            "duplicate_records": duplicate_records,
            "execution_time_seconds": duration,
            "status": "Failed",
            "message": f"ETL Pipeline Error: {str(e)}"
        }
    finally:
        conn.close()

def get_etl_history(limit=20):
    """Retrieves recent ETL batch runs."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT BatchID, FileName, TotalRecords, AcceptedRecords,
                   RejectedRecords, DuplicateRecords, ExecutionTimeSeconds,
                   Status, Details, CreatedAt
            FROM ETLHistory
            ORDER BY CreatedAt DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_staging_errors(batch_id=None, limit=50):
    """Retrieves rejected/duplicate rows from StagingTransactions."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if batch_id:
            cursor.execute("""
                SELECT StagingID, BatchID, InvoiceNo, CustomerID, ProductID,
                       Quantity, UnitPrice, ValidationStatus, ErrorMessage, ImportedAt
                FROM StagingTransactions
                WHERE ValidationStatus != 'Valid' AND BatchID = ?
                ORDER BY StagingID DESC
                LIMIT ?
            """, (batch_id, limit))
        else:
            cursor.execute("""
                SELECT StagingID, BatchID, InvoiceNo, CustomerID, ProductID,
                       Quantity, UnitPrice, ValidationStatus, ErrorMessage, ImportedAt
                FROM StagingTransactions
                WHERE ValidationStatus != 'Valid'
                ORDER BY StagingID DESC
                LIMIT ?
            """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
