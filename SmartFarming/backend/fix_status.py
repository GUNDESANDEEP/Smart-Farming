import mysql.connector

conn = mysql.connector.connect(
    host='localhost', user='root', 
    password='sandeep@7981', database='SmartFarmingDB'
)
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE farmers ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
    conn.commit()
    print("Added status to farmers")
except Exception as e:
    print(f"farmers status: {e}")

try:
    cur.execute("ALTER TABLE buyers ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
    conn.commit()
    print("Added status to buyers")
except Exception as e:
    print(f"buyers status: {e}")

cur.close()
conn.close()
print("Done!")
