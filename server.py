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

urlLisensi= "http://156.67.216.77:5001"

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
@app.route('/add_license', methods=['POST'])
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
          "is_valid": False
        }), 400
    
    if not license['start_time']:
        expired_time = date + timedelta(days=license['active_time'])
        cursor.execute("UPDATE Licenses SET start_time = %s, expired_time = %s WHERE license_key = %s AND script = %s",
                       (date, expired_time, license_key, script))
        conn.commit()
        return jsonify({
            "status": "Login successful",
            "url": urlLisensi,
            "start_time": date.strftime('%Y-%m-%d %H:%M:%S'),
            "expired_time": expired_time.strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    else:
        expired_time = license['expired_time']
        if date < expired_time:
            return jsonify({
                "status": "Login successful",
                "url": urlLisensi,
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

@app.route('/controlDb', methods=['GET'])
@auth.login_required
def control_db():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Licenses")
    licenses = cursor.fetchall()
    conn.close()
  
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>License Control</title>
    </head>
    <body>
        <h1>License Control</h1>
        <table border="1">
            <tr>
                <th>ID</th>
                <th>License Key</th>
                <th>Script</th>
                <th>Active Time</th>
                <th>Start Time</th>
                <th>Expired Time</th>
                <th>Actions</th>
            </tr>
            {% for license in licenses %}
            <tr>
                <td>{{ license['id'] }}</td>
                <td>{{ license['license_key'] }}</td>
                <td>{{ license['script'] }}</td>
                <td>{{ license['active_time'] }}</td>
                <td>{{ license['start_time'] }}</td>
                <td>{{ license['expired_time'] }}</td>
                <td>
                    <form action="/edit_license/{{ license['id'] }}" method="post">
                        <input type="hidden" name="id" value="{{ license['id'] }}">
                        <input type="text" name="license_key" value="{{ license['license_key'] }}">
                        <input type="text" name="script" value="{{ license['script'] }}">
                        <input type="text" name="active_time" value="{{ license['active_time'] }}">
                        <input type="text" name="start_time" value="{{ license['start_time'] }}">
                        <input type="text" name="expired_time" value="{{ license['expired_time'] }}">
                        <input type="submit" value="Edit">
                    </form>
                    <form action="/delete_license/{{ license['id'] }}" method="post" onsubmit="return confirm('Are you sure you want to delete this license?');">
                        <input type="hidden" name="id" value="{{ license['id'] }}">
                        <input type="submit" value="Delete">
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''
    return render_template_string(html, licenses=licenses)

# Endpoint untuk mengedit lisensi
@app.route('/edit_license/<int:id>', methods=['POST'])
@auth.login_required
def edit_license(id):
    data = request.form
    license_key = data.get('license_key')
    script = data.get('script')
    active_time = data.get('active_time')
    start_time = data.get('start_time')
    expired_time = data.get('expired_time')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        UPDATE Licenses 
        SET license_key = %s, script = %s, active_time = %s, start_time = %s, expired_time = %s 
        WHERE id = %s
    """, (license_key, script, active_time, start_time, expired_time, id))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "License updated successfully"}), 200

# Endpoint untuk menghapus lisensi
@app.route('/delete_license/<int:id>', methods=['POST'])
@auth.login_required
def delete_license(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("DELETE FROM Licenses WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "License deleted successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
