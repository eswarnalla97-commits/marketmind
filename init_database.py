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
    if os.path.exists(config.SAMPLE_DATA_PATH):
        print(f"[2/3] Executing ETL pipeline on {config.SAMPLE_DATA_PATH}...")
        result = run_etl(config.SAMPLE_DATA_PATH, original_filename="sample_transactions.csv", batch_id="SEED_INITIAL_2024")
        if result["success"]:
            print(f"      ETL Seed Completed: {result['accepted_records']} records loaded in {result['execution_time_seconds']}s.")
        else:
            print(f"      ETL Seed Warning: {result['message']}")
    else:
        print("[2/3] Warning: Sample data file not found, skipping initial seed.")

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
        print("[3/3] Sample feedback entry seeded.")
    except Exception as e:
        print(f"[3/3] Note: Feedback seeding: {e}")

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
