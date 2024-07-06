from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)

# MySQL database connection
def get_db_connection():
    connection = mysql.connector.connect(
        host='156.67.216.77',
        user='bagas',
        password='your_password',
        database='lisensiScript'
    )
    return connection

# POST request to add license
@app.route('/add_license', methods=['POST'])
def add_license():
    data = request.json
    license_key = data.get('license_key')
    active_time = int(data.get('active_time'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Check if the license key already exists
    cursor.execute("SELECT * FROM Licenses WHERE license_key = %s", (license_key,))
    license = cursor.fetchone()
    if license:
        conn.close()
        return jsonify({"status": "License key already exists"}), 400
    # Insert new license into database
    cursor.execute("INSERT INTO Licenses (license_key, active_time) VALUES (%s, %s)", 
                   (license_key, active_time))
    
    conn.commit()
    conn.close()
    
    return jsonify({"status": "License added successfully",
                    "license_key": license_key,
                    "active_time": active_time}), 200

# GET request to login and update start time if necessary
@app.route('/login/<license_key>', methods=['GET'])
def login(license_key):
    date_str = request.args.get('date')
    date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM Licenses WHERE license_key = %s", (license_key,))
    license = cursor.fetchone()
    
    if not license:
        return jsonify({"status": "Invalid license key"}), 400
    
    if not license['start_time']:
        expired_time = date + timedelta(days=license['active_time'])
        cursor.execute("UPDATE Licenses SET start_time = %s, expired_time = %s WHERE license_key = %s",
                       (date, expired_time, license_key))
        conn.commit()
        return jsonify({
            "status": "Login successful",
            "start_time": date.strftime('%Y-%m-%d %H:%M:%S'),
            "expired_time": expired_time.strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    else:
        expired_time = license['expired_time']
        if date < expired_time:
            return jsonify({
                "status": "Login successful",
                "start_time": license['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
                "expired_time": expired_time.strftime('%Y-%m-%d %H:%M:%S'),
                "is_valid": True
            }), 200
        else:
            return jsonify({
                "status": "License expired",
                "expired_time": expired_time.strftime('%Y-%m-%d %H:%M:%S'),
                "is_valid": False
            }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
      
