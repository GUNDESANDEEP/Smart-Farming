import psycopg2
from dotenv import load_dotenv
import os
load_dotenv('.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("UPDATE buyers SET email='gundesandeep2005@gmail.com' WHERE phone='9347538630'")
conn.commit()
print("Buyer email updated to gundesandeep2005@gmail.com")
cur.close()
conn.close()
