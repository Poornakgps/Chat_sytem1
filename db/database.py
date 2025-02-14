import sqlite3

def get_db_connection():
    return sqlite3.connect('chat.db')

def create_tables():
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS buyer_chat
            (chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            file_name TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_bargain BOOLEAN DEFAULT FALSE,
            bargain_amount FLOAT,
            payment_status TEXT DEFAULT 'pending')''')
            
        c.execute('''CREATE TABLE IF NOT EXISTS seller_chat
            (chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            file_name TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            order_status TEXT,
            bargain_status TEXT,
            payment_status TEXT,
            payment_qr_code TEXT)''')
            
        conn.commit()
    finally:
        conn.close()

def insert_buyer_chat(message, file_name, is_bargain, bargain_amount, payment_status):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''INSERT INTO buyer_chat (message, file_name, is_bargain, bargain_amount, payment_status)
                    VALUES (?, ?, ?, ?, ?)''', (message, file_name, is_bargain, bargain_amount, payment_status))
        conn.commit()
    finally:
        conn.close()

def insert_seller_chat(message, file_name, order_status, bargain_status, payment_status, payment_qr_code):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''INSERT INTO seller_chat (message, file_name, order_status, bargain_status, payment_status, payment_qr_code)
                    VALUES (?, ?, ?, ?, ?, ?)''', (message, file_name, order_status, bargain_status, payment_status, payment_qr_code))
        conn.commit()
    finally:
        conn.close()

def get_chat_history(user_type):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        table = "buyer_chat" if user_type == "buyer" else "seller_chat"
        c.execute(f'SELECT * FROM {table} ORDER BY timestamp DESC LIMIT 50')
        return c.fetchall()
    finally:
        conn.close()
