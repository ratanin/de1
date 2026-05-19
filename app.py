from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'baandee_secret_key'
DB_NAME = 'Rental_management.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# เช็กและอัปเดตตารางฐานข้อมูลโดยอัตโนมัติ
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. ตรวจสอบตาราง Rooms และเพิ่มคอลัมน์ใหม่หากยังไม่มีในฐานข้อมูลเดิม
    try:
        cursor.execute("ALTER TABLE Rooms ADD COLUMN condo_name TEXT DEFAULT 'Baandee Condo'")
    except sqlite3.OperationalError:
        pass  # มีคอลัมน์อยู่แล้ว
        
    try:
        cursor.execute("ALTER TABLE Rooms ADD COLUMN room_size REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass  # 有คอลัมน์อยู่แล้ว

    # ⭐ เพิ่มคอลัมน์สำหรับเก็บอีเมลผู้เช่า (Tenant Email)
    try:
        cursor.execute("ALTER TABLE Rooms ADD COLUMN tenant_email TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # มีคอลัมน์อยู่แล้ว

    # 2. ตารางที่ 4: Payments (ระบบรับชำระเงิน)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER,
            amount REAL,
            payment_date TEXT,
            payment_status TEXT,
            FOREIGN KEY (room_id) REFERENCES Rooms (room_id)
        )
    ''')

    # ตารางที่ 5: MaintenanceRequests (ระบบแจ้งซ่อม)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS MaintenanceRequests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER,
            description TEXT,
            request_date TEXT,
            status TEXT,
            FOREIGN KEY (room_id) REFERENCES Rooms (room_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# เรียกใช้งานการตั้งค่า Database
init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    # ดึงข้อมูลมาแสดงที่หน้าแรก (รวม tenant_email มาด้วย)
    rentals = conn.execute('SELECT * FROM Rooms').fetchall()
    conn.close()
    return render_template('index.html', rentals=rentals)

@app.route('/add', methods=['GET', 'POST'])
def add_rental():
    if request.method == 'POST':
        room_number = request.form['room_number']
        condo_name = request.form['condo_name']
        room_size = request.form['room_size']
        tenant_name = request.form['tenant_name']
        tenant_phone = request.form['tenant_phone']
        tenant_email = request.form['tenant_email']  # ⭐ รับค่าอีเมลจากฟอร์มหน้าเว็บ
        monthly_rent = request.form['monthly_rent']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        room_image_url = request.form['room_image_url']

        conn = get_db_connection()
        # ⭐ เพิ่ม tenant_email เข้าไปในคำสั่ง INSERT
        conn.execute('''
            INSERT INTO Rooms (room_number, condo_name, room_size, tenant_name, tenant_phone, tenant_email, monthly_rent, start_date, end_date, room_image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (room_number, condo_name, room_size, tenant_name, tenant_phone, tenant_email, monthly_rent, start_date, end_date, room_image_url))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
        
    return render_template('add_rental.html')

@app.route('/edit/<int:room_id>', methods=['GET', 'POST'])
def edit_rental(room_id):
    conn = get_db_connection()
    rental = conn.execute('SELECT * FROM Rooms WHERE room_id = ?', (room_id,)).fetchone()

    if request.method == 'POST':
        room_number = request.form['room_number']
        condo_name = request.form['condo_name']
        room_size = request.form['room_size']
        tenant_name = request.form['tenant_name']
        tenant_phone = request.form['tenant_phone']
        tenant_email = request.form['tenant_email']  # ⭐ รับค่าอีเมลที่แก้ไขจากฟอร์ม
        monthly_rent = request.form['monthly_rent']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        room_image_url = request.form['room_image_url']

        # ⭐ เพิ่ม tenant_email เข้าไปในคำสั่ง UPDATE
        conn.execute('''
            UPDATE Rooms 
            SET room_number = ?, condo_name = ?, room_size = ?, tenant_name = ?, tenant_phone = ?, tenant_email = ?, monthly_rent = ?, start_date = ?, end_date = ?, room_image_url = ?
            WHERE room_id = ?
        ''', (room_number, condo_name, room_size, tenant_name, tenant_phone, tenant_email, monthly_rent, start_date, end_date, room_image_url, room_id))
        conn.commit()
        conn.close()
        return redirect(url_for('view_rental', room_id=room_id))

    conn.close()
    return render_template('edit.html', rental=rental)

@app.route('/view/<int:room_id>')
def view_rental(room_id):
    conn = get_db_connection()
    rental = conn.execute('SELECT * FROM Rooms WHERE room_id = ?', (room_id,)).fetchone()
    payments = conn.execute('SELECT * FROM Payments WHERE room_id = ? ORDER BY payment_date DESC', (room_id,)).fetchall()
    maintenance = conn.execute('SELECT * FROM MaintenanceRequests WHERE room_id = ? ORDER BY request_date DESC', (room_id,)).fetchall()
    conn.close()
    return render_template('view_rental.html', rental=rental, payments=payments, maintenance=maintenance)

@app.route('/delete/<int:room_id>', methods=['POST'])
def delete_rental(room_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Rooms WHERE room_id = ?', (room_id,))
    conn.execute('DELETE FROM Payments WHERE room_id = ?', (room_id,))
    conn.execute('DELETE FROM MaintenanceRequests WHERE room_id = ?', (room_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/reset/<int:room_id>', methods=['POST'])
def reset_rental(room_id):
    conn = get_db_connection()
    conn.execute('''
        UPDATE Rooms 
        SET tenant_name='', tenant_phone='', tenant_email='', monthly_rent=NULL, start_date=NULL, end_date=NULL 
        WHERE room_id=?
    ''', (room_id,))
    conn.execute('DELETE FROM Payments WHERE room_id = ?', (room_id,))
    conn.execute('DELETE FROM MaintenanceRequests WHERE room_id = ?', (room_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_rental', room_id=room_id))

@app.route('/payments', methods=['GET', 'POST'])
def payments():
    conn = get_db_connection()
    if request.method == 'POST':
        room_id = request.form['room_id']
        amount = request.form['amount']
        payment_date = request.form['payment_date']
        payment_status = request.form['payment_status']
        conn.execute("INSERT INTO Payments (room_id, amount, payment_date, payment_status) VALUES (?, ?, ?, ?)", (room_id, amount, payment_date, payment_status))
        conn.commit()
        return redirect(url_for('payments'))
    payments = conn.execute('SELECT p.*, r.room_number FROM Payments p JOIN Rooms r ON p.room_id = r.room_id ORDER BY p.payment_date DESC').fetchall()
    rooms = conn.execute("SELECT room_id, room_number FROM Rooms").fetchall()
    conn.close()
    return render_template('payments.html', payments=payments, rooms=rooms)

@app.route('/maintenance', methods=['GET', 'POST'])
def maintenance():
    conn = get_db_connection()
    if request.method == 'POST':
        room_id = request.form['room_id']
        description = request.form['description']
        request_date = request.form['request_date']
        status = request.form['status']
        conn.execute("INSERT INTO MaintenanceRequests (room_id, description, request_date, status) VALUES (?, ?, ?, ?)", (room_id, description, request_date, status))
        conn.commit()
        return redirect(url_for('maintenance'))
    requests = conn.execute('SELECT m.*, r.room_number FROM MaintenanceRequests m JOIN Rooms r ON m.room_id = r.room_id ORDER BY m.request_date DESC').fetchall()
    rooms = conn.execute("SELECT room_id, room_number FROM Rooms").fetchall()
    conn.close()
    return render_template('maintenance.html', requests=requests, rooms=rooms)

@app.route('/maintenance/update/<int:request_id>/<string:status>')
def update_maintenance(request_id, status):
    conn = get_db_connection()
    conn.execute("UPDATE MaintenanceRequests SET status = ? WHERE request_id = ?", (status, request_id))
    conn.commit()
    conn.close()
    return redirect(url_for('maintenance'))

if __name__ == '__main__':
    app.run(debug=True)