from flask import Flask, request, jsonify
import mysql.connector
import bcrypt
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# database config
db_config = {
    'user': 'root',
    'password': '1234',
    'host': 'localhost',
    'database': 'your_database_name'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# 1. User management

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = data['password']
    email = data['email']
    
    #bcrypt password hashing
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)", 
                       (username, hashed, email))
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERRE username = %s", (data['username'],))
    user = cursor.fetchone()
    conn.close()
    
    if user and brcypt.checkpw(data['password'].encode('utf-8'), user['password_hash'].encode('utf-8')):
        return jsonify({"message": "Login successful", "user_id": user['id'], "role": user['role']}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# 2. Book management and Search

@app.route('/books', methods=['GET'])
def search_books():
    keyword = request.args.get('q', '')
    query = "SELECT * FROM books WHERE title LIKE %s OR author LIKE %s"
    wildcard = f"%{keyword}%"
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, (wildcard, wildcard))
    books = cursor.fetchall()
    conn.close()
    return jsonify(books)

@app.route('/books', methods=['POST'])
def add_book():
    # managers only
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO books (title, author, buy_price, rent_price) VALUES (%s, %s, %s, %s)",
                   (data['title'], data['author'], data['buy_price'], data['rent_price']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Book added successfully"}), 201

# 3. Orders and Billing
# external SMTP
def send_email_notification(email, order_id, total):
    msg = MIMEText(f"Thank you for your order #{order_id}. Total due: ${total}")
    msg['Subject'] = "Order Confirmation"
    msg['From'] = "noreply@bookstore.com"
    msg['To'] = email

@app.route('/orders', methods=['POST'])
def place_order():
    data = request.json
    user_id = data['user_id']
    items = data['items']
    
    total = sum(item['price'] for item in items)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO orders (user_id, total_amount, status) VALUES (%s, %s, 'Pending')", (user_id, total))
    order_id = cursor.lastrowid
    
    for item in items:
        cursor.execute("INSERT INTO order_items (order_id, book_id, type, price_at_time) VALUES (%s, %s, %s, %s)",
                       (order_id, item['book_id'], item['type'], item['price']))    
    
    conn.commit()
    
    #fetch email notif
    cursor.execute("SELECT email FROM users WHERE id=%s", (user_id,))
    email = cursor.fetchone()[0]
    conn.close()
    
    send_email_notification(email, order_id, total)
    
    return jsonify({"message": "Order placed successfully", "order_id": order_id}), 201

@app.route('/orders', methods=['GET'])
def get_orders():
    # manager function to view orders
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT o.id, u.username, o.total_amount, o.status
        FROM orders o
        JOIN users u ON o.user_id = u.id               
    """)
    orders = cursor.fetchall()
    conn.close()
    return jsonify(orders)

@app.route('/orders/<int:order_id>/pay', methods=['PUT'])
def update_payment(order_id):
    # manager fucntion to update payment statuses
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status='Paid' WHERE id=%s", (order_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Order marked as Paid"}), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)

