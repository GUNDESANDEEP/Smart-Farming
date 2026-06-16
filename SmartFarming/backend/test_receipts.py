import requests
r = requests.post('http://localhost:8000/api/auth/login', json={'email':'gundesandeep2005@gmail.com','password':'Sandy@7981','role':'admin'})
t = r.json()['access_token']
r2 = requests.get('http://localhost:8000/api/admin/receipts', headers={'Authorization':'Bearer '+t})
data = r2.json()
rcpts = data.get('receipts', [])
print(f"Status: {r2.status_code}, Count: {len(rcpts)}")
for r in rcpts[:3]:
    print(f"  {r.get('receipt_id','?')} buyer={r.get('buyer_name','?')} farmer={r.get('farmer_name','?')} product={r.get('product_name','?')}")
