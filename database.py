import sqlite3
import json
import secrets

DB_FILE = "validation_history.db"


# -----------------------------
# INIT DATABASE
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Validation history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS validation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT,
            supplier_id TEXT,
            po_number TEXT,
            status TEXT,
            score INTEGER,
            summary TEXT,
            decision_json TEXT,
            errors_json TEXT,
            warnings_json TEXT,
            passed_rules_json TEXT
        )
    """)

    # Usage tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_tracking (
            api_key TEXT PRIMARY KEY,
            usage_count INTEGER NOT NULL
        )
    """)

    # Clients
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            api_key TEXT PRIMARY KEY,
            client_name TEXT NOT NULL,
            plan TEXT NOT NULL,
            max_usage INTEGER NOT NULL,
            is_paid INTEGER DEFAULT 0
        )
    """)

    # Ensure backward compatibility (add column if missing)
    cursor.execute("PRAGMA table_info(clients)")
    columns = [row[1] for row in cursor.fetchall()]

    if "is_paid" not in columns:
        cursor.execute("""
            ALTER TABLE clients
            ADD COLUMN is_paid INTEGER DEFAULT 0
        """)

    conn.commit()
    conn.close()


# -----------------------------
# SEED DEFAULT CLIENTS
# -----------------------------
def seed_default_clients():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    default_clients = [
        ("my-secret-key", "Demo Free Client", "FREE", 5, 0),
        ("pro-secret-key", "Demo Pro Client", "PRO", 100, 1),
        ("enterprise-secret-key", "Demo Enterprise Client", "ENTERPRISE", 1000, 1)
    ]

    for client in default_clients:
        cursor.execute("""
            INSERT OR IGNORE INTO clients (api_key, client_name, plan, max_usage, is_paid)
            VALUES (?, ?, ?, ?, ?)
        """, client)

    conn.commit()
    conn.close()


# -----------------------------
# VALIDATION HISTORY
# -----------------------------
def save_validation_result(result):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO validation_history (
            invoice_number,
            supplier_id,
            po_number,
            status,
            score,
            summary,
            decision_json,
            errors_json,
            warnings_json,
            passed_rules_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        result["invoice_number"],
        result["supplier_id"],
        result["po_number"],
        result["status"],
        result["score"],
        result["summary"],
        json.dumps(result["decision"]),
        json.dumps(result["errors"]),
        json.dumps(result["warnings"]),
        json.dumps(result["passed_rules"])
    ))

    conn.commit()
    conn.close()


def get_all_validation_history():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            invoice_number,
            supplier_id,
            po_number,
            status,
            score,
            summary,
            decision_json,
            errors_json,
            warnings_json,
            passed_rules_json
        FROM validation_history
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    history = []
    for row in rows:
        history.append({
            "id": row[0],
            "invoice_number": row[1],
            "supplier_id": row[2],
            "po_number": row[3],
            "status": row[4],
            "score": row[5],
            "summary": row[6],
            "decision": json.loads(row[7]),
            "errors": json.loads(row[8]),
            "warnings": json.loads(row[9]),
            "passed_rules": json.loads(row[10])
        })

    return history


# -----------------------------
# USAGE TRACKING
# -----------------------------
def get_usage_count(api_key: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT usage_count
        FROM usage_tracking
        WHERE api_key = ?
    """, (api_key,))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else 0


def increment_usage_count(api_key: str):
    current_count = get_usage_count(api_key)
    new_count = current_count + 1

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO usage_tracking (api_key, usage_count)
        VALUES (?, ?)
        ON CONFLICT(api_key) DO UPDATE SET usage_count = excluded.usage_count
    """, (api_key, new_count))

    conn.commit()
    conn.close()

    return new_count


def reset_usage_count(api_key: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO usage_tracking (api_key, usage_count)
        VALUES (?, 0)
        ON CONFLICT(api_key) DO UPDATE SET usage_count = 0
    """, (api_key,))

    conn.commit()
    conn.close()


# -----------------------------
# CLIENT MANAGEMENT
# -----------------------------
def get_client_by_api_key(api_key: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT api_key, client_name, plan, max_usage, is_paid
        FROM clients
        WHERE api_key = ?
    """, (api_key,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "api_key": row[0],
        "client_name": row[1],
        "plan": row[2],
        "max_usage": row[3],
        "is_paid": row[4]
    }


def get_all_clients():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT api_key, client_name, plan, max_usage, is_paid
        FROM clients
        ORDER BY client_name
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "api_key": row[0],
            "client_name": row[1],
            "plan": row[2],
            "max_usage": row[3],
            "is_paid": row[4]
        }
        for row in rows
    ]


def create_client(client_name: str, plan: str, max_usage: int):
    api_key = secrets.token_urlsafe(24)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO clients (api_key, client_name, plan, max_usage, is_paid)
        VALUES (?, ?, ?, ?, ?)
    """, (api_key, client_name, plan, max_usage, 0))

    conn.commit()
    conn.close()

    return {
        "api_key": api_key,
        "client_name": client_name,
        "plan": plan,
        "max_usage": max_usage,
        "is_paid": 0
    }


def update_client_plan(api_key: str, plan: str, max_usage: int, is_paid: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE clients
        SET plan = ?, max_usage = ?, is_paid = ?
        WHERE api_key = ?
    """, (plan, max_usage, is_paid, api_key))

    conn.commit()
    conn.close()