import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Users Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    phone TEXT,
    password TEXT,
    address TEXT,
    pincode TEXT
)
""")

# Products Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price INTEGER,
    description TEXT    
)
""")

# Colors Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS colors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    color_name TEXT,
    image TEXT,
    FOREIGN KEY(product_id) REFERENCES products(id)
)
""")

# Sizes Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS sizes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    size TEXT,
    FOREIGN KEY(product_id) REFERENCES products(id)
)
""")

# Orders Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT,
    customer_name TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    pincode TEXT,
    total INTEGER,
    status TEXT,
    payment TEXT,
    date TEXT,
    time TEXT
)
""")

# Order Items Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT,
    product_name TEXT,
    color TEXT,
    size TEXT,
    quantity INTEGER,
    price INTEGER,
    image TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    product_id INTEGER,
    product_name TEXT,
    color TEXT,
    size TEXT,
    quantity INTEGER,
    price INTEGER,
    image TEXT
)
""")
conn.commit()
conn.close()

print("All tables created successfully!")