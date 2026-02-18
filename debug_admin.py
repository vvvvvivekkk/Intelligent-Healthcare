"""Direct SQLite debug - no Flask imports"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'medsync.db')
out = []
out.append(f"DB path: {db_path}")
out.append(f"DB exists: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # List all tables
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    out.append(f"Tables: {[t['name'] for t in tables]}")
    
    # Check if admins table exists
    table_names = [t['name'] for t in tables]
    if 'admins' in table_names:
        rows = conn.execute("SELECT * FROM admins").fetchall()
        out.append(f"Admins rows: {len(rows)}")
        for r in rows:
            keys = r.keys()
            out.append(f"  Columns: {keys}")
            out.append(f"  id={r['id']}, username='{r['username']}', hash='{r['password_hash'][:50]}...'")
    else:
        out.append("*** ADMINS TABLE DOES NOT EXIST ***")
        out.append("Creating it now...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        out.append("Table created.")
        
        # Now insert admin
        from werkzeug.security import generate_password_hash
        h = generate_password_hash('admin123')
        conn.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)", ('admin', h))
        conn.commit()
        out.append(f"Admin inserted with hash: {h[:50]}...")
    
    conn.close()
else:
    out.append("DATABASE FILE NOT FOUND!")

result = '\n'.join(out)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debug_output.txt'), 'w') as f:
    f.write(result)
print(result)
