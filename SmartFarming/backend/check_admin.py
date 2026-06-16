import mysql.connector
from mysql.connector import Error

try:
    # Connect to MySQL
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Sandy@7981',
        database='SmartFarmingDB'
    )
    
    cursor = conn.cursor(dictionary=True)
    
    # Check if admins table exists
    cursor.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'SmartFarmingDB' AND TABLE_NAME = 'admins'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        print('✓ Admins table exists')
        # Count admins
        cursor.execute('SELECT COUNT(*) as count FROM admins')
        result = cursor.fetchone()
        print(f'Total admins: {result["count"]}')
        
        # Show all admins
        cursor.execute('SELECT admin_id, email, first_name, role FROM admins')
        admins = cursor.fetchall()
        for admin in admins:
            print(f'  - ID: {admin["admin_id"]}, Email: {admin["email"]}, Name: {admin["first_name"]}, Role: {admin["role"]}')
    else:
        print('✗ Admins table does not exist')
    
    cursor.close()
    conn.close()
except Error as e:
    print(f'✗ Database connection error: {e}')
