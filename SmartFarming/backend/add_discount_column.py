import mysql.connector
conn = mysql.connector.connect(host='localhost', user='root', password='sandeep@7981', database='SmartFarmingDB')
cur = conn.cursor()
try:
    cur.execute('ALTER TABLE products ADD COLUMN discount_percent INT DEFAULT 0')
    conn.commit()
    print('Added discount_percent column')
except Exception as e:
    print('Column may exist:', e)
cur.close()
conn.close()
