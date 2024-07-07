from flask import Flask, request, jsonify, render_template_string
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
@app.route('/add_license', methods=['POST'])
@auth.login_required
def add_license():
    data = request.json if request.is_json else request.form
    license_key = data.get('license_key')
    active_time = int(data.get('active_time'))
    script = data.get('script')
    license_url = data.get('license_url')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if the license key already exists
    cursor.execute("SELECT * FROM Licenses WHERE license_key = %s AND script = %s", (license_key, script))
    license = cursor.fetchone()
    if license:
        conn.close()
        return jsonify({"status": "License key already exists"}), 400
    
    # Insert new license into database
    cursor.execute("INSERT INTO Licenses (license_key, active_time, script, license_url) VALUES (%s, %s, %s, %s)", 
                   (license_key, active_time, script, license_url))
    
    conn.commit()
    conn.close()
    
    return jsonify({"status": "License added successfully",
                    "license_key": license_key,
                    "active_time": active_time,
                    "script": script,
                    "license_url": license_url}), 200

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
            "url": license['license_url'],
            "start_time": date.strftime('%Y-%m-%d %H:%M:%S'),
            "expired_time": expired_time.strftime('%Y-%m-%d %H:%M:%S'),
            "is_valid": True
        }), 200
    else:
        expired_time = license['expired_time']
        if date < expired_time:
            return jsonify({
                "status": "Login successful",
                "url": license['license_url'],
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
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f9;
                margin: 0;
                padding: 20px;
            }
            h1, h2 {
                color: #333;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            table, th, td {
                border: 1px solid #ccc;
            }
            th, td {
                padding: 10px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            form {
                display: inline-block;
            }
            input[type="text"], input[type="number"] {
                padding: 5px;
                margin: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            input[type="submit"] {
                padding: 5px 10px;
                margin: 5px;
                border: 1px solid #28a745;
                background-color: #28a745;
                color: white;
                border-radius: 3px;
                cursor: pointer;
            }
            input[type="submit"]:hover {
                background-color: #218838;
            }
        </style>
    </head>
    <body>
        <h1>License Control</h1>
        <table>
            <tr>
                <th>ID</th>
                <th>License Key</th>
                <th>Script</th>
                <th>Active Time</th>
                <th>Start Time</th>
                <th>Expired Time</th>
                <th>License URL</th>
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
                <td>{{ license['license_url'] }}</td>
                <td>
                    <form action="/edit_license/{{ license['id'] }}" method="post">
                        <input type="hidden" name="id" value="{{ license['id'] }}">
                        <input type="text" name="license_key" value="{{ license['license_key'] }}">
                        <input type="text" name="script" value="{{ license['script'] }}">
                        <input type="text" name="active_time" value="{{ license['active_time'] }}">
                        <input type="text" name="start_time" value="{{ license['start_time'] }}">
                        <input type="text" name="expired_time" value="{{ license['expired_time'] }}">
                        <input type="text" name="license_url" value="{{ license['license_url'] }}">
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
        <h2>Add New License</h2>
        <form action="/add_license" method="post">
            <input type="text" name="license_key" placeholder="License Key" required>
            <input type="text" name="script" placeholder="Script" required>
            <input type="number" name="active_time" placeholder="Active Time (days)" required>
            <input type="text" name="license_url" placeholder="License URL" required>
            <input type="submit" value="Add License">
        </form>
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
    license_url = data.get('license_url')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        UPDATE Licenses 
        SET license_key = %s, script = %s, active_time = %s, start_time = %s, expired_time = %s, license_url = %s 
        WHERE id = %s
    """, (license_key, script, active_time, start_time, expired_time, license_url, id))
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

# Endpoint to serve the content of the ghost.lua file
@app.route('/', methods=['GET'])
def serve_ghost_lua():
    with open('ghost.lua', 'r') as file:
        content = file.read()
    return render_template_string('<pre>{{ content }}</pre>', content=content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
