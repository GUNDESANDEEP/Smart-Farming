import urllib.request
import urllib.error
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    'https://smartfarming-marketplace.onrender.com/api',
    'https://smartfarming-marketplace.onrender.com/api/health',
    'https://smartfarming-marketplace.onrender.com/api/auth/send-otp'
]

print("Checking active backend with 75 seconds timeout (handling cold start)...")
for u in urls:
    print(f"\n--- Checking: {u} ---")
    try:
        req = urllib.request.Request(
            u,
            data=b'{}' if 'send-otp' in u else None,
            headers={'Content-Type': 'application/json'} if 'send-otp' in u else {}
        )
        with urllib.request.urlopen(req, timeout=75, context=ctx) as r:
            print(f"RESPONSE: Status {r.status}")
            print(f"HEADERS: {dict(r.headers)}")
            try:
                body = r.read().decode('utf-8')
                print(f"BODY: {body[:1000]}")
            except Exception as e:
                print(f"Failed to read body: {e}")
    except urllib.error.HTTPError as e:
        print(f"HTTP ERROR: Status {e.code}")
        print(f"HEADERS: {dict(e.headers)}")
        try:
            print(f"BODY: {e.read().decode('utf-8')[:1000]}")
        except Exception as read_err:
            print(f"Failed to read error body: {read_err}")
    except Exception as e:
        print(f"ERROR: {e}")
