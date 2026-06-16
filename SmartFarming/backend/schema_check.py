import MySQLdb
import MySQLdb.cursors

conn = MySQLdb.connect(host='localhost', user='root', password='sandeep@7981', db='SmartFarmingDB', charset='utf8mb4')
cursor = conn.cursor(MySQLdb.cursors.DictCursor)

# Get all tables
cursor.execute("SHOW TABLES")
tables = cursor.fetchall()
print("=" * 60)
print("DATABASE SCHEMA: SmartFarmingDB")
print("=" * 60)

for table in tables:
    table_name = list(table.values())[0]
    print(f"\n--- TABLE: {table_name} ---")
    cursor.execute(f"DESCRIBE {table_name}")
    columns = cursor.fetchall()
    for col in columns:
        nullable = "NULL" if col['Null'] == 'YES' else "NOT NULL"
        key = col['Key'] if col['Key'] else ""
        default = f"DEFAULT {col['Default']}" if col['Default'] else ""
        extra = col['Extra'] if col['Extra'] else ""
        print(f"  {col['Field']:30s} {col['Type']:25s} {nullable:8s} {key:4s} {default} {extra}")
    
    # Count rows
    cursor.execute(f"SELECT COUNT(*) as cnt FROM {table_name}")
    count = cursor.fetchone()['cnt']
    print(f"  >> Rows: {count}")

conn.close()
