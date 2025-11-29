import logging
import datetime
from yoyo import read_migrations
from src.config.settings import Config
import pyodbc
import uuid
import getpass
import socket

# Configure logging
logging.basicConfig(level=logging.INFO)

def manual_fake_apply(migrations):
    conn_str = (
        f"DRIVER={Config.DB_DRIVER};"
        f"SERVER={Config.DB_SERVER};"
        f"DATABASE={Config.DB_NAME};"
        f"Trusted_Connection={Config.DB_TRUSTED_CONNECTION};"
        "TrustServerCertificate=yes;"
    )
    
    print(f"Connecting to {Config.DB_SERVER}...")
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        for m in migrations:
            print(f"Marking {m.id} ({m.hash}) as applied...")
            
            # Check if already applied
            cursor.execute("SELECT count(*) FROM _yoyo_migration WHERE migration_hash = ?", (m.hash,))
            if cursor.fetchone()[0] > 0:
                print(f"  Already applied.")
                continue
            
            # Insert into _yoyo_migration
            cursor.execute(
                "INSERT INTO _yoyo_migration (migration_hash, migration_id, applied_at_utc) VALUES (?, ?, ?)",
                (m.hash, m.id, datetime.datetime.utcnow())
            )
            
            # Insert into _yoyo_log
            log_id = str(uuid.uuid1())
            cursor.execute(
                "INSERT INTO _yoyo_log (id, migration_id, migration_hash, username, hostname, created_at_utc, operation) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (log_id, m.id, m.hash, getpass.getuser(), socket.getfqdn(), datetime.datetime.utcnow(), 'mark')
            )
            
        conn.commit()
        conn.close()
        print("✅ Manual fake apply completed.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def run_migrations(fake=False):
    migrations = read_migrations('migrations')
    
    if fake:
        manual_fake_apply(migrations)
    else:
        print("Real apply not implemented in this script due to yoyo/SQLServer issues. Use manual apply if needed.")

if __name__ == "__main__":
    import sys
    fake_mode = "--fake" in sys.argv
    run_migrations(fake=fake_mode)
