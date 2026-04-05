"""
migrate_to_mysql.py
-------------------
Run this ONCE when you are on the same network as 192.168.7.21.
It will:
  1. Test the MySQL connection
  2. Run all Django migrations on MySQL (creates all tables)
  3. Export all data from SQLite
  4. Import that data into MySQL

Usage:
    venv\Scripts\python.exe migrate_to_mysql.py
"""

import os
import sys
import subprocess

PYTHON = sys.executable

def run(cmd, env=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    return result.returncode

# ── Step 1: Test MySQL connection ─────────────────────────────────────────────
print("\n[1/4] Testing MySQL connection...")
try:
    import MySQLdb
    conn = MySQLdb.connect(
        host='192.168.7.21', user='student', passwd='1432',
        db='student_management_db', connect_timeout=5
    )
    cur = conn.cursor()
    cur.execute('SELECT VERSION()')
    version = cur.fetchone()[0]
    cur.execute('SHOW TABLES')
    existing_tables = [t[0] for t in cur.fetchall()]
    conn.close()
    print(f"    Connected! MySQL {version}")
    print(f"    Existing tables: {len(existing_tables)}")
except Exception as e:
    print(f"    FAILED: {e}")
    print("\n    Make sure you are on the same network as 192.168.7.21 and the MySQL server is running.")
    sys.exit(1)

# ── Step 2: Run migrations on MySQL ──────────────────────────────────────────
print("\n[2/4] Running migrations on MySQL...")
rc = run(f'"{PYTHON}" manage.py migrate --database=default')
if rc != 0:
    print("    Migration failed. Fix errors above and retry.")
    sys.exit(1)
print("    Migrations complete.")

# ── Step 3: Export data from SQLite ──────────────────────────────────────────
print("\n[3/4] Exporting data from SQLite...")
env = os.environ.copy()
env['USE_SQLITE'] = '1'
rc = run(
    f'"{PYTHON}" manage.py dumpdata '
    '--natural-foreign --natural-primary '
    '--exclude auth.permission --exclude contenttypes '
    '--indent 2 '
    '-o sqlite_export.json',
    env=env
)
if rc != 0:
    print("    Export failed.")
    sys.exit(1)

import json
with open('sqlite_export.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f"    Exported {len(data)} records to sqlite_export.json")

# ── Step 4: Import into MySQL ─────────────────────────────────────────────────
print("\n[4/4] Importing data into MySQL...")
rc = run(f'"{PYTHON}" manage.py loaddata sqlite_export.json --database=default')
if rc != 0:
    print("    Import failed. Check errors above.")
    sys.exit(1)

print("\n✅ Migration complete! All SQLite data is now in MySQL.")
print("   sqlite_export.json kept as backup.")
print("   db.sqlite3 untouched.")
