# MarketMind — E-commerce Customer Behavior Mining and Sales Analytics Portal

**MarketMind** is a full-stack web analytics portal engineered for a **B.Tech CSE Data Warehousing and Data Mining (DWDM)** mini project. Built according to **Indian retail standards**, it natively operates in **Indian Rupee (INR - ₹)** using the **Indian Numbering System (`en-IN` Lakhs / Crores)**, with transactions distributed across major Indian states and commercial hubs.

It integrates a Kimball Star Schema data warehouse, an automated ETL pipeline, Online Analytical Processing (OLAP) multidimensional cube operations, and unsupervised data mining algorithms:
- **Apriori Association Mining** (using `mlxtend`) for Market Basket cross-sell discovery.
- **K-Means Behavioral Clustering** (using `scikit-learn`) for customer RFM segmentation.

---

## 1. System Architecture & Star Schema

```
[ Raw CSV Files / User Uploads ]
               │
               ▼
   [ ETL Cleansing & Validation Pipeline ]
         │                        │
         ▼                        ▼
[ Validated Records ]    [ Staging Area (Dirty / Duplicates) ]
         │
         ▼
┌────────────────────────────────────────────────────────┐
│             SQLite STAR SCHEMA DATA WAREHOUSE          │
│                                                        │
│   DimDate ───────┐                  ┌────── DimCustomer│
│   (DateKey)      │                  │      (CustomerKey)
│                  ▼                  ▼                  │
│               [       FactSales       ]                │
│               [ Grain: 1 Order Item   ]                │
│                  ▲                  ▲                  │
│   DimProduct ────┘                  └────── DimOrder   │
│   (ProductKey)                             (OrderKey)  │
└────────────────────────────────────────────────────────┘
         │                                       │
         ▼                                       ▼
  [ OLAP Query Engine ]               [ Machine Learning Mining ]
  - Roll-Up (Daily->Yearly)           - Apriori Association Rules
  - Drill-Down (Cat->SKU)             - K-Means Customer RFM
  - Slice (1D Plane)                  - Support, Confidence, Lift
  - Dice (Multi-D Sub-Cube)           - Normalized Centroids
  - Pivot (Cross-Tab Matrix)
         │                                       │
         └───────────────────┬───────────────────┘
                             ▼
              [ Flask REST API & Web Views ]
                             │
                             ▼
     [ Responsive Multi-Page Bootstrap 5 Portal ]
```

### Star Schema Tables & Grain
- **Grain:** Exactly **1 row per order line item** in `FactSales`. This prevents double-counting order totals during dimensional joins while preserving granular basket contents.
- **`FactSales`**: `SalesKey`, `DateKey`, `CustomerKey`, `ProductKey`, `OrderKey`, `Quantity`, `UnitPrice`, `DiscountAmount`, `TotalAmount`, `ProfitMargin`.
- **`DimDate`**: `DateKey` (YYYYMMDD), `FullDate`, `Day`, `Month`, `MonthName`, `Quarter`, `Year`, `DayOfWeek`, `DayName`, `IsWeekend`.
- **`DimProduct`**: `ProductKey`, `ProductID`, `ProductName`, `Category`, `UnitPrice`.
- **`DimCustomer`**: `CustomerKey`, `CustomerID`, `CustomerName`, `Country`, `Segment`, `FirstPurchaseDate`.
- **`DimOrder`**: `OrderKey`, `InvoiceNo`, `OrderDate`, `TotalItems`, `TotalOrderValue`, `OrderStatus`.
- **`StagingTransactions`**: Captures dirty records, invalid prices, and duplicate line items.
- **`ETLHistory`**: Audit trail of every batch ingestion with execution time, row counts, and status.
- **`FeedbackSubmissions`**: Stores viva evaluator remarks and user inquiries.

---

## 2. Multi-Page Website Portal Structure

| Page | Route | Description |
|---|---|---|
| **Page 1: Public Home Page** | `/` | Product landing page with hero, live metrics ticker, feature highlights, ETL workflow diagram, and tech stack. |
| **Page 2: About & DWDM** | `/about` | Problem statement, project objectives, star schema details, OLAP concepts, Apriori & K-Means mathematical models. |
| **Page 3: Analytics Dashboard** | `/dashboard` | 5 KPI summary cards, Monthly Revenue chart, Category donut chart, Geographic bar chart, Top products table, dynamic Year/Category filters. |
| **Page 4: ETL Portal** | `/data-import` | Drag & drop CSV ingestion, schema validation, staging error inspection, batch audit log, and downloadable templates. |
| **Page 5: Association Mining** | `/product-mining` | Apriori algorithm with sliders for Min Support & Min Confidence, Frequent Bundles, Lift vs Confidence scatter plot, and natural-language rule translations. |
| **Page 6: Customer Segmentation**| `/customer-segmentation`| K-Means clustering ($K=2$ to $6$) on standardized RFM features, persona cards (Champions, Loyalists, At-Risk, Occasional), spend distribution charts, and customer roster table. |
| **Page 7: OLAP Analytics** | `/olap` | Interactive Roll-up, Drill-down, Slice, Dice, and Pivot matrix with a live **SQL Query Inspector** showing the exact executed queries. |
| **Page 8: Reports & Insights** | `/reports` | Consolidated Executive Reports for Sales, Products, Customers, and Association Rules with one-click CSV export and print layouts. |
| **Page 9: Contact & Viva** | `/contact` | Academic credentials, course information, interactive feedback form that saves submissions into SQLite, and a live feedback log. |

---

## 3. Technology Stack

- **Backend:** Python 3.10+, Flask 3.1
- **Data Engineering:** pandas, numpy, SQLite3
- **Data Mining & ML:** `mlxtend` (Apriori algorithm), `scikit-learn` (StandardScaler & KMeans)
- **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Chart.js 4.4, Font Awesome 6
- **Testing:** Python `unittest` test suite (26 automated tests)

---

## 4. Mandatory Windows Run Instructions (VS Code & PowerShell)

### Step 1: Prerequisites
Make sure you have:
1. **Windows 10 or Windows 11**
2. **Python 3.10 or higher** installed and added to your system `PATH`.
3. **Visual Studio Code** installed.

Verify Python in PowerShell:
```powershell
python --version
```

---

### Step 2: Open Project in VS Code
1. Launch **VS Code**.
2. Go to **File -> Open Folder...** and select `d:\marketmind` (or your cloned folder).
3. Open a PowerShell terminal in VS Code: press ``Ctrl + ` `` (Backtick) or go to **Terminal -> New Terminal**.

---

### Step 3: Create & Activate Virtual Environment
In your VS Code PowerShell terminal, run:
```powershell
# Create virtual environment named 'venv'
python -m venv venv

# If PowerShell script execution is restricted on Windows, allow it for this process:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Activate the virtual environment
.\venv\Scripts\Activate.ps1
```
*(Your prompt will now show `(venv)` at the beginning).*

---

### Step 4: Install Dependencies
Install all required libraries using `pip`:
```powershell
pip install -r requirements.txt
```
*Packages installed:* `Flask`, `pandas`, `numpy`, `scikit-learn`, `mlxtend`, `Werkzeug`.

---

### Step 5: Initialize Database & Seed Sample Data
Run the database setup script to create the Star Schema and execute the initial ETL pipeline on the bundled 1,282 sample transactions:
```powershell
python init_database.py
```
**Expected Output:**
```
==================================================
MarketMind: Initializing Data Warehouse Database
==================================================
[1/3] Schema created successfully.
[2/3] Executing ETL pipeline on ...\sample_transactions.csv...
      ETL Seed Completed: 1282 records loaded in 0.92s.
[3/3] Sample feedback entry seeded.
==================================================
Data Warehouse Initial Statistics:
 - FactSales             : 1282 records
 - DimCustomer           : 160 records
 - DimProduct            : 28 records
 - DimDate               : 293 records
 - DimOrder              : 647 records
==================================================
Initialization completed successfully!
```

---

### Step 6: Start the MarketMind Web Server
Start the Flask application:
```powershell
python app.py
```
**Expected Output:**
```
==================================================
MarketMind Web Portal Starting on http://127.0.0.1:5000
==================================================
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

---

### Step 7: Access the Portal in Your Web Browser
Open your browser (Chrome, Edge, Firefox) and navigate to:
```
http://127.0.0.1:5000
```

### Direct URLs for Each Page:
- **Home:** [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **About & DWDM:** [http://127.0.0.1:5000/about](http://127.0.0.1:5000/about)
- **Analytics Dashboard:** [http://127.0.0.1:5000/dashboard](http://127.0.0.1:5000/dashboard)
- **Data Import & ETL:** [http://127.0.0.1:5000/data-import](http://127.0.0.1:5000/data-import)
- **Product Mining (Apriori):** [http://127.0.0.1:5000/product-mining](http://127.0.0.1:5000/product-mining)
- **Customer Segmentation (K-Means):** [http://127.0.0.1:5000/customer-segmentation](http://127.0.0.1:5000/customer-segmentation)
- **OLAP Analytics:** [http://127.0.0.1:5000/olap](http://127.0.0.1:5000/olap)
- **Executive Reports:** [http://127.0.0.1:5000/reports](http://127.0.0.1:5000/reports)
- **Contact & Feedback:** [http://127.0.0.1:5000/contact](http://127.0.0.1:5000/contact)

---

### Step 8: How to Upload Another CSV Dataset
1. Navigate to the **ETL Portal** at [http://127.0.0.1:5000/data-import](http://127.0.0.1:5000/data-import).
2. Click **Download Template CSV** to review the expected headers (`InvoiceNo`, `InvoiceDate`, `CustomerID`, `ProductID`, `ProductName`, `Category`, `Quantity`, `UnitPrice`, `Country`).
3. Drag & drop your new `.csv` file into the upload dropzone.
4. The system validates headers and counts rows immediately.
5. Click **Run Complete ETL Pipeline**.
6. The portal cleans dirty rows, isolates duplicates, updates dimensions, and loads `FactSales`.
7. Check the **ETL Batch Execution History** and **Staging Area Rejections** tabs for the audit log.

---

### Step 9: How to Run the Automated Test Suite
Open a separate terminal window in VS Code and run:
```powershell
python tests\run_tests.py
```
**Expected Output:**
```
==================================================
Running MarketMind Comprehensive Test Suite
==================================================
test_etl_history_retrieval (test_etl.TestETL) ... ok
test_validate_valid_csv (test_etl.TestETL) ... ok
test_apriori_execution (test_mining.TestDataMining) ... ok
test_kmeans_execution (test_mining.TestDataMining) ... ok
test_page_1_home (test_routes.TestRoutes) ... ok
test_page_3_dashboard (test_routes.TestRoutes) ... ok
...
Ran 26 tests in 1.055s
OK
SUCCESS: All 26 tests passed successfully!
==================================================
```

---

### Step 10: How to Stop the Server
In the PowerShell terminal running `python app.py`:
- Press `Ctrl + C`.

---

## 5. Windows Troubleshooting Guide

| Issue | Cause | Solution |
|---|---|---|
| **`Execution of scripts is disabled on this system`** | Windows PowerShell execution policy blocks virtual environment activation. | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in your PowerShell window, then run `.\venv\Scripts\Activate.ps1`. |
| **`Address already in use: 5000`** | Another application (or background Flask process) is using port 5000. | In PowerShell, find and kill the process: <br> `Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess \| Stop-Process -Force` |
| **`No module named 'mlxtend'` or `'sklearn'`** | Package not installed in the currently active environment. | Ensure venv is active and run: <br> `pip install pandas scikit-learn mlxtend Flask` |
| **`Database locked`** | Multiple processes writing to SQLite simultaneously. | Stop secondary instances of `app.py` or restart the terminal. SQLite connections in `db_manager.py` automatically release cursors with safe `try...finally` blocks. |
| **`CSV Upload says "Missing required columns"`** | Uploaded CSV has misspelled headers. | Check against the 9 required columns: `InvoiceNo, InvoiceDate, CustomerID, ProductID, ProductName, Category, Quantity, UnitPrice, Country`. |

---

## 6. DWDM Academic Viva Highlights

When presenting this project to evaluators:
1. **Explain the Star Schema:** Show `schema.sql` and the **SQL Query Inspector** on the OLAP page (`/olap`). Highlight the item-level grain that avoids double-counting order totals.
2. **Demonstrate Apriori:** Go to `/product-mining`. Adjust the Min Support slider from 2% down to 1% to demonstrate candidate generation and observe rules with Lift $> 2.0$ (e.g. Mechanical Keyboard + Ergonomic Mouse).
3. **Demonstrate K-Means:** Go to `/customer-segmentation`. Explain that features (`Recency`, `Frequency`, `Monetary`, `AOV`) are normalized with `StandardScaler` so monetary scale doesn't overpower frequency.
4. **Demonstrate OLAP:** Go to `/olap`. Click **Roll-Up**, **Drill-Down**, **Slice**, **Dice**, and **Pivot** while showing the dynamically generated SQL query box!
