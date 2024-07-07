from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)
auth = HTTPBasicAuth()

# In-memory user data
users = {
    "bagasW": "Bagas030208"
}

@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None

# MySQL database connection
def get_db_connection():
    connection = mysql.connector.connect(
        host='156.67.216.77',
        user='bagas',
        password='your_password',
        database='lisensiScript'
    )
    return connection

# POST request to add license with Basic Authentication
@app.route('/add_licenseBagasWAdminAddLisensi7777', methods=['POST'])
@auth.login_required
def add_license():
    data = request.json
    license_key = data.get('license_key')
    active_time = int(data.get('active_time'))
    script = data.get('script')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if the license key already exists
    cursor.execute("SELECT * FROM Licenses WHERE license_key = %s AND script = %s", (license_key, script))
    license = cursor.fetchone()
    if license:
        conn.close()
        return jsonify({"status": "License key already exists"}), 400
    
    # Insert new license into database
    cursor.execute("INSERT INTO Licenses (license_key, active_time, script) VALUES (%s, %s, %s)", 
                   (license_key, active_time, script))
    
    conn.commit()
    conn.close()
    
    return jsonify({"status": "License added successfully",
                    "license_key": license_key,
                    "active_time": active_time,
                    "script": script}), 200

# GET request to login and update start time if necessary
@app.route('/login/<script>/<license_key>', methods=['GET'])
def login(script, license_key):
    date_str = request.args.get('date')
    date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM Licenses WHERE license_key = %s AND script = %s", (license_key, script))
    license = cursor.fetchone()
    
    if not license:
        return jsonify({"status": "Invalid license key",
          "is_valid": True
        }), 400
    
    if not license['start_time']:
        expired_time = date + timedelta(days=license['active_time'])
        cursor.execute("UPDATE Licenses SET start_time = %s, expired_time = %s WHERE license_key = %s AND script = %s",
                       (date, expired_time, license_key, script))
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

# GET request to display and control all licenses with Basic Authentication
@app.route('/controlDb', methods=['GET', 'POST', 'DELETE', 'PUT'])
@auth.login_required
def control_db():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'GET':
        # Get all licenses
        cursor.execute("SELECT * FROM Licenses")
        licenses = cursor.fetchall()
        conn.close()
        return jsonify(licenses), 200

    elif request.method == 'POST':
        # Add a new license (reusing the add_license logic)
        data = request.json
        license_key = data.get('license_key')
        active_time = int(data.get('active_time'))
        script = data.get('script')
        
        # Check if the license key already exists
        cursor.execute("SELECT * FROM Licenses WHERE license_key = %s AND script = %s", (license_key, script))
        license = cursor.fetchone()
        if license:
            conn.close()
            return jsonify({"status": "License key already exists"}), 400
        
        # Insert new license into database
        cursor.execute("INSERT INTO Licenses (license_key, active_time, script) VALUES (%s, %s, %s)", 
                       (license_key, active_time, script))
        
        conn.commit()
        conn.close()
        
        return jsonify({"status": "License added successfully",
                        "license_key": license_key,
                        "active_time": active_time,
                        "script": script}), 200

    elif request.method == 'DELETE':
        # Delete a license
        data = request.json
        license_key = data.get('license_key')
        script = data.get('script')
        
        cursor.execute("DELETE FROM Licenses WHERE license_key = %s AND script = %s", (license_key, script))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "License deleted successfully"}), 200

    elif request.method == 'PUT':
        # Update a license
        data = request.json
        license_key = data.get('license_key')
        script = data.get('script')
        new_active_time = int(data.get('active_time'))
        
        cursor.execute("UPDATE Licenses SET active_time = %s WHERE license_key = %s AND script = %s", 
                       (new_active_time, license_key, script))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "License updated successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
