import pyodbc
from src.config.settings import Config

def init_tables():
    conn_str = (
        f"DRIVER={Config.DB_DRIVER};"
        f"SERVER={Config.DB_SERVER};"
        f"DATABASE={Config.DB_NAME};"
        f"Trusted_Connection={Config.DB_TRUSTED_CONNECTION};"
        "TrustServerCertificate=yes;"
    )
    
    print(f"Connecting to {Config.DB_SERVER}...")
    try:
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        
        # yoyo_lock
        print("Creating yoyo_lock...")
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[yoyo_lock]') AND type in (N'U'))
            BEGIN
                CREATE TABLE yoyo_lock (
                    locked INT PRIMARY KEY,
                    ctime DATETIME,
                    pid INT
                );
                INSERT INTO yoyo_lock (locked, ctime, pid) VALUES (1, NULL, NULL);
            END
        """)
        
        # _yoyo_migration
        print("Creating _yoyo_migration...")
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[_yoyo_migration]') AND type in (N'U'))
            BEGIN
                CREATE TABLE _yoyo_migration (
                    migration_hash VARCHAR(64) PRIMARY KEY,
                    migration_id VARCHAR(255),
                    applied_at_utc DATETIME
                );
            END
        """)
        
        # _yoyo_log
        print("Creating _yoyo_log...")
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[_yoyo_log]') AND type in (N'U'))
            BEGIN
                CREATE TABLE _yoyo_log (
                    id VARCHAR(36) PRIMARY KEY,
                    migration_id VARCHAR(255),
                    migration_hash VARCHAR(64),
                    username VARCHAR(255),
                    hostname VARCHAR(255),
                    created_at_utc DATETIME,
                    operation VARCHAR(10)
                );
            END
        """)
        
        print("Tables initialized successfully.")
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    init_tables()
