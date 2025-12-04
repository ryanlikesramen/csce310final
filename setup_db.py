import mysql.connector
import bcrypt

# --- CONFIGURATION ---
# Enter the exact same settings you used in your backend.py
db_config = {
    'user': 'bookstore_admin',   # OR 'root' if you went with Option 2
    'password': '1234',   # YOUR MySQL password
    'host': 'localhost',
}

def init_db():
    print("Connecting to MySQL...")
    # Connect to MySQL Server (no database selected yet)
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # 1. Create Database
    print("Creating database 'bookstore_db'...")
    cursor.execute("CREATE DATABASE IF NOT EXISTS bookstore_db")
    cursor.execute("USE bookstore_db")

    # 2. Create Tables
    print("Creating tables...")
    
    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        email VARCHAR(100) NOT NULL,
        role ENUM('customer', 'manager') DEFAULT 'customer'
    )
    """)

    # Books Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        author VARCHAR(255) NOT NULL,
        buy_price DECIMAL(10, 2) NOT NULL,
        rent_price DECIMAL(10, 2) NOT NULL,
        stock INT DEFAULT 1
    )
    """)

    # Orders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        total_amount DECIMAL(10, 2),
        status ENUM('Pending', 'Paid') DEFAULT 'Pending',
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # Order Items Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        order_id INT,
        book_id INT,
        type ENUM('buy', 'rent'),
        price_at_time DECIMAL(10, 2),
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (book_id) REFERENCES books(id)
    )
    """)

    # 3. Insert Admin User (With Hashed Password)
    print("Checking for admin user...")
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        print("Creating default admin user...")
        password = "admin123"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username, password_hash, email, role) VALUES (%s, %s, %s, %s)", 
                       ('admin', hashed, 'admin@store.com', 'manager'))
    else:
        print("Admin user already exists.")

    conn.commit()
    conn.close()
    print("SUCCESS! Database setup complete.")

if __name__ == "__main__":
    try:
        init_db()
    except mysql.connector.Error as err:
        print(f"Error: {err}")