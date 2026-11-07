import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "dx_quest.db")

def view_table(table_name):
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Get column names
        cur.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cur.fetchall()]

        if not columns:
            print(f"❌ Table '{table_name}' does not exist or is empty.")
            return

        # Fetch data
        cur.execute(f"SELECT * FROM {table_name}")
        rows = cur.fetchall()

        print(f"\n--- Table: {table_name} ({len(rows)} rows) ---")
        # Print Headers
        header_line = " | ".join(columns)
        print(header_line)
        print("-" * len(header_line))

        # Print Rows
        for row in rows:
            print(" | ".join(str(item) for item in row))
        print("\n")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "challenges"
    view_table(target)
