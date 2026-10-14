import os
from database.db_manager import init_db, get_warehouse_stats, execute_commit
from etl.etl_pipeline import run_etl
from config import config

def setup_and_seed():
    print("==================================================")
    print("MarketMind: Initializing Data Warehouse Database")
    print("==================================================")
    
    # 1. Initialize schema
    init_db()
    print("[1/3] Schema created successfully.")

    # 2. Seed with sample transactions via ETL
    from database.db_manager import query_scalar
    fact_count = query_scalar("SELECT COUNT(*) FROM FactSales") or 0
    if fact_count == 0 and os.path.exists(config.SAMPLE_DATA_PATH):
        print(f"[2/4] Executing ETL pipeline on {config.SAMPLE_DATA_PATH}...")
        result = run_etl(config.SAMPLE_DATA_PATH, original_filename="sample_transactions.csv", batch_id="SEED_INITIAL_2024")
        if result["success"]:
            print(f"      ETL Seed Completed: {result['accepted_records']} records loaded in {result['execution_time_seconds']}s.")
        else:
            print(f"      ETL Seed Warning: {result['message']}")
    elif fact_count > 0:
        print(f"[2/4] Star Schema already populated ({fact_count} fact records), skipping initial seed.")
    else:
        print("[2/4] Warning: Sample data file not found, skipping initial seed.")

    # 3. Insert demo feedback entry
    try:
        execute_commit("""
            INSERT INTO FeedbackSubmissions (Name, Email, Category, Subject, Message, Rating, Status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Academic Evaluator",
            "evaluator@university.edu",
            "Viva Feedback",
            "Impressive Star Schema & Mining Architecture",
            "The multi-dimensional OLAP analysis, Apriori rule extraction, and K-Means segmentation demonstrate sound DWDM principles.",
            5,
            "Reviewed"
        ))
        print("[3/4] Sample feedback entry seeded.")
    except Exception as e:
        print(f"[3/4] Note: Feedback seeding: {e}")

    # 4. Seed default admin, analyst, and viewer users
    try:
        from database.db_manager import query_scalar
        from werkzeug.security import generate_password_hash
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
            from database.admin_service import DEFAULT_SETTINGS, log_activity
            for k, v in DEFAULT_SETTINGS.items():
                execute_commit("INSERT OR IGNORE INTO SystemSettings (SettingKey, SettingValue) VALUES (?, ?)", (k, v))
            log_activity('System', 'Database Initialization', 'StarSchema', 'DW_INIT', 'Initialized Star Schema, default administrator accounts, and settings.')
            print("[4/4] Default admin accounts and settings seeded.")
        else:
            print("[4/4] Admin user accounts already present.")
    except Exception as e:
        print(f"[4/4] Note: Admin seeding: {e}")

    # Display stats
    stats = get_warehouse_stats()
    print("==================================================")
    print("Data Warehouse Initial Statistics:")
    for table, count in stats.items():
        print(f" - {table.ljust(22)}: {count} records")
    print("==================================================")
    print("Initialization completed successfully!")

if __name__ == "__main__":
    setup_and_seed()
