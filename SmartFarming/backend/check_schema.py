import psycopg2, os
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'), connect_timeout=10)
cur = conn.cursor()

for table in ['orders', 'order_tracking', 'cart', 'cart_items', 'return_requests', 'buyer_reviews', 'payments', 'wallet', 'transactions']:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position", (table,))
    cols = [r[0] for r in cur.fetchall()]
    if cols:
        print(f"{table}: {', '.join(cols)}")
    else:
        print(f"{table}: TABLE DOES NOT EXIST")
    print()

cur.close()
conn.close()
