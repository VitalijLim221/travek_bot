import sqlite3
import json
from bot.config import DATABASE_PATH
from bot.crypto_utils import encrypt_data, decrypt_data


def init_database():
    "Initialize the database with required tables"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE NOT NULL,
            name TEXT,
            phone TEXT,
            points INTEGER DEFAULT 0,
            interests TEXT,
            current_route TEXT,
            visited_objects TEXT,
            route_step INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create shop items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shop_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price INTEGER NOT NULL,
            category TEXT,
            image_url TEXT,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    conn.commit()
    conn.close()


def save_user(tg_id, name, phone):
    "Save or update user information"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    encrypted_name = encrypt_data(name)
    encrypted_phone = encrypt_data(phone)

    cursor.execute('''
        INSERT OR REPLACE INTO users (tg_id, name, phone, points, interests, current_route, visited_objects, route_step)
        VALUES (?, ?, ?, 
                COALESCE((SELECT points FROM users WHERE tg_id = ?), 0),
                COALESCE((SELECT interests FROM users WHERE tg_id = ?), ''),
                COALESCE((SELECT current_route FROM users WHERE tg_id = ?), ''),
                COALESCE((SELECT visited_objects FROM users WHERE tg_id = ?), '[]'),
                COALESCE((SELECT route_step FROM users WHERE tg_id = ?), 0))
    ''', (tg_id, encrypted_name, encrypted_phone, tg_id, tg_id, tg_id, tg_id, tg_id))

    conn.commit()
    conn.close()


def get_user(tg_id):
    "Get user information"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    row = cursor.fetchone()

    if row:
        # Decrypt sensitive data
        decrypted_row = list(row)
        decrypted_row[2] = decrypt_data(row[2])  # name
        decrypted_row[3] = decrypt_data(row[3])  # phone

        # Parse JSON fields
        try:
            decrypted_row[6] = json.loads(row[6]) if row[6] else []  # current_route
        except:
            decrypted_row[6] = []

        try:
            decrypted_row[7] = json.loads(row[7]) if row[7] else []  # visited_objects
        except:
            decrypted_row[7] = []

        conn.close()
        return decrypted_row

    conn.close()
    return None


def update_user_interests(tg_id, interests):
    "Update user interests"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET interests = ? WHERE tg_id = ?", (interests, tg_id))
    conn.commit()
    conn.close()


def update_user_route(tg_id, route):
    "Update user current route"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    route_json = json.dumps(route)
    cursor.execute("UPDATE users SET current_route = ?, route_step = 0 WHERE tg_id = ?",
                   (route_json, tg_id))
    conn.commit()
    conn.close()


def get_user_route(tg_id):
    "Get user current route"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT current_route FROM users WHERE tg_id = ?", (tg_id,))
    row = cursor.fetchone()

    if row and row[0]:
        try:
            return json.loads(row[0])
        except:
            return []

    conn.close()
    return []


def update_route_step(tg_id, step):
    "Update current route step"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET route_step = ? WHERE tg_id = ?", (step, tg_id))
    conn.commit()
    conn.close()


def get_route_step(tg_id):
    "Get current route step"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT route_step FROM users WHERE tg_id = ?", (tg_id,))
    row = cursor.fetchone()

    conn.close()
    return row[0] if row else 0


def add_visited_object(tg_id, obj):
    "Add visited object to user's list"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Get current visited objects
    cursor.execute("SELECT visited_objects FROM users WHERE tg_id = ?", (tg_id,))
    row = cursor.fetchone()

    if row:
        try:
            visited = json.loads(row[0]) if row[0] else []
        except:
            visited = []

        visited.append(obj)
        visited_json = json.dumps(visited)

        cursor.execute("UPDATE users SET visited_objects = ? WHERE tg_id = ?",
                       (visited_json, tg_id))
        conn.commit()

    conn.close()


def add_points(tg_id, points):
    "Add points to user"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET points = points + ? WHERE tg_id = ?", (points, tg_id))
    conn.commit()
    conn.close()


def get_all_users():
    "Get all users (for admin panel)"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    # Decrypt sensitive data
    decrypted_rows = []
    for row in rows:
        decrypted_row = list(row)
        decrypted_row[2] = decrypt_data(row[2])  # name
        decrypted_row[3] = decrypt_data(row[3])  # phone
        decrypted_rows.append(decrypted_row)

    conn.close()
    return decrypted_rows


def get_shop_items(active_only=True):
    "Get all shop items"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    if active_only:
        cursor.execute("SELECT * FROM shop_items WHERE is_active = 1 ORDER BY price")
    else:
        cursor.execute("SELECT * FROM shop_items ORDER BY price")

    rows = cursor.fetchall()
    conn.close()
    return rows


def add_shop_item(name, description, price, category, image_url=None):
    "Add new shop item"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO shop_items (name, description, price, category, image_url, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
    ''', (name, description, price, category, image_url))

    conn.commit()
    conn.close()


def update_shop_item(item_id, name, description, price, category, image_url=None, is_active=True):
    "Update shop item"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE shop_items 
        SET name = ?, description = ?, price = ?, category = ?, image_url = ?, is_active = ?
        WHERE id = ?
    ''', (name, description, price, category, image_url, is_active, item_id))

    conn.commit()
    conn.close()


def delete_shop_item(item_id):
    "Delete shop item"
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM shop_items WHERE id = ?", (item_id,))

    conn.commit()
    conn.close()


# Initialize database on import
#init_database()