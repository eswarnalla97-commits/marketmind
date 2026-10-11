-- MarketMind E-Commerce Data Warehouse Star Schema & Staging Tables

-- Enable Foreign Key constraints
PRAGMA foreign_keys = ON;

-- ============================================================================
-- 1. DIMENSION TABLES
-- ============================================================================

-- Dimension: Customer
CREATE TABLE IF NOT EXISTS DimCustomer (
    CustomerKey INTEGER PRIMARY KEY AUTOINCREMENT,
    CustomerID TEXT NOT NULL UNIQUE,
    CustomerName TEXT NOT NULL,
    Country TEXT NOT NULL,
    Segment TEXT DEFAULT 'Standard',
    FirstPurchaseDate TEXT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Product
CREATE TABLE IF NOT EXISTS DimProduct (
    ProductKey INTEGER PRIMARY KEY AUTOINCREMENT,
    ProductID TEXT NOT NULL UNIQUE,
    ProductName TEXT NOT NULL,
    Category TEXT NOT NULL,
    UnitPrice REAL NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Date
CREATE TABLE IF NOT EXISTS DimDate (
    DateKey INTEGER PRIMARY KEY, -- Format: YYYYMMDD
    FullDate TEXT NOT NULL UNIQUE, -- Format: YYYY-MM-DD
    Day INTEGER NOT NULL,
    Month INTEGER NOT NULL,
    MonthName TEXT NOT NULL,
    Quarter INTEGER NOT NULL,
    Year INTEGER NOT NULL,
    DayOfWeek INTEGER NOT NULL,
    DayName TEXT NOT NULL,
    IsWeekend INTEGER NOT NULL -- 1 if Saturday/Sunday, else 0
);

-- Dimension: Order
CREATE TABLE IF NOT EXISTS DimOrder (
    OrderKey INTEGER PRIMARY KEY AUTOINCREMENT,
    InvoiceNo TEXT NOT NULL UNIQUE,
    OrderDate TEXT NOT NULL,
    TotalItems INTEGER DEFAULT 0,
    TotalOrderValue REAL DEFAULT 0.0,
    OrderStatus TEXT DEFAULT 'Completed',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. FACT TABLE (Grain: 1 record per Order Line Item)
-- ============================================================================

CREATE TABLE IF NOT EXISTS FactSales (
    SalesKey INTEGER PRIMARY KEY AUTOINCREMENT,
    DateKey INTEGER NOT NULL,
    CustomerKey INTEGER NOT NULL,
    ProductKey INTEGER NOT NULL,
    OrderKey INTEGER NOT NULL,
    Quantity INTEGER NOT NULL,
    UnitPrice REAL NOT NULL,
    DiscountAmount REAL DEFAULT 0.0,
    TotalAmount REAL NOT NULL,
    ProfitMargin REAL DEFAULT 0.25,
    FOREIGN KEY (DateKey) REFERENCES DimDate(DateKey) ON DELETE CASCADE,
    FOREIGN KEY (CustomerKey) REFERENCES DimCustomer(CustomerKey) ON DELETE CASCADE,
    FOREIGN KEY (ProductKey) REFERENCES DimProduct(ProductKey) ON DELETE CASCADE,
    FOREIGN KEY (OrderKey) REFERENCES DimOrder(OrderKey) ON DELETE CASCADE
);

-- Create Indexes for OLAP query performance
CREATE INDEX IF NOT EXISTS idx_fact_date ON FactSales(DateKey);
CREATE INDEX IF NOT EXISTS idx_fact_customer ON FactSales(CustomerKey);
CREATE INDEX IF NOT EXISTS idx_fact_product ON FactSales(ProductKey);
CREATE INDEX IF NOT EXISTS idx_fact_order ON FactSales(OrderKey);
CREATE INDEX IF NOT EXISTS idx_dimdate_year_month ON DimDate(Year, Month);
CREATE INDEX IF NOT EXISTS idx_dimproduct_category ON DimProduct(Category);

-- ============================================================================
-- 3. STAGING AREA & ETL LOGGING
-- ============================================================================

CREATE TABLE IF NOT EXISTS StagingTransactions (
    StagingID INTEGER PRIMARY KEY AUTOINCREMENT,
    BatchID TEXT NOT NULL,
    InvoiceNo TEXT,
    InvoiceDate TEXT,
    CustomerID TEXT,
    ProductID TEXT,
    ProductName TEXT,
    Category TEXT,
    Quantity REAL,
    UnitPrice REAL,
    Country TEXT,
    ValidationStatus TEXT DEFAULT 'Pending', -- Valid, Rejected, Duplicate
    ErrorMessage TEXT,
    ImportedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ETLHistory (
    BatchID TEXT PRIMARY KEY,
    FileName TEXT NOT NULL,
    TotalRecords INTEGER NOT NULL,
    AcceptedRecords INTEGER NOT NULL,
    RejectedRecords INTEGER NOT NULL,
    DuplicateRecords INTEGER NOT NULL,
    ExecutionTimeSeconds REAL NOT NULL,
    Status TEXT NOT NULL, -- Success, Partial, Failed
    Details TEXT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 4. FEEDBACK & CONTACT SUBMISSIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS FeedbackSubmissions (
    FeedbackID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Email TEXT NOT NULL,
    Category TEXT NOT NULL,
    Subject TEXT NOT NULL,
    Message TEXT NOT NULL,
    Rating INTEGER DEFAULT 5,
    Status TEXT DEFAULT 'New',
    SubmittedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
