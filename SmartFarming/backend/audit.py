"""
PHASE 1: Complete Project Audit Script
Scans entire codebase and reports all issues
"""
import os
import re
import sys

BACKEND_DIR = r"c:\Users\SANDEEP\OneDrive\Farming MARK\SmartFarming\backend"
FRONTEND_DIR = r"C:\Users\SANDEEP\OneDrive\Documents\Desktop\Smart Farming\SmartFarming\frontend"

report = []

def section(title):
    report.append(f"\n{'='*60}")
    report.append(f"  {title}")
    report.append(f"{'='*60}")

# 1. Check for duplicate/conflicting files
section("1. FILE INVENTORY")
backend_files = []
for root, dirs, files in os.walk(BACKEND_DIR):
    dirs[:] = [d for d in dirs if d not in ('__pycache__', 'node_modules', '.git', 'venv')]
    for f in files:
        if f.endswith(('.py', '.env', '.json', '.sql')):
            rel = os.path.relpath(os.path.join(root, f), BACKEND_DIR)
            size = os.path.getsize(os.path.join(root, f))
            backend_files.append((rel, size))
            report.append(f"  {rel:50s} {size:>8,} bytes")

# 2. Check app.py imports
section("2. APP.PY ANALYSIS")
app_path = os.path.join(BACKEND_DIR, "app.py")
with open(app_path, 'r') as f:
    app_content = f.read()

imports = re.findall(r'from\s+([\w.]+)\s+import\s+(.+)', app_content)
for mod, names in imports:
    report.append(f"  Import: from {mod} import {names.strip()}")

blueprints = re.findall(r'register_blueprint\((\w+)', app_content)
report.append(f"\n  Registered Blueprints: {', '.join(blueprints)}")

# Check which imported modules exist
for mod, names in imports:
    if mod.startswith('routes.'):
        route_file = os.path.join(BACKEND_DIR, mod.replace('.', os.sep) + '.py')
        exists = os.path.exists(route_file)
        status = "OK" if exists else "MISSING!"
        report.append(f"  [{status}] {mod} -> {route_file}")
    elif mod.startswith('models.'):
        model_file = os.path.join(BACKEND_DIR, mod.replace('.', os.sep) + '.py')
        exists = os.path.exists(model_file)
        status = "OK" if exists else "MISSING!"
        report.append(f"  [{status}] {mod} -> {model_file}")

# Check socket_events
se_path = os.path.join(BACKEND_DIR, "socket_events.py")
report.append(f"\n  socket_events.py exists: {os.path.exists(se_path)}")

# 3. Environment variables
section("3. ENVIRONMENT VARIABLES")
env_path = os.path.join(BACKEND_DIR, ".env")
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key = line.split('=')[0]
                val = line.split('=', 1)[1] if '=' in line else ''
                is_placeholder = val in ('', 'your-secret-key-here', 'your-email@gmail.com', 
                    'your-app-password', 'your-razorpay-key', 'your-razorpay-secret',
                    'your-weather-api-key', 'your-twilio-sid', 'your-twilio-token',
                    '+1234567890', 'your-aws-key', 'your-aws-secret', 'your-bucket-name')
                status = "PLACEHOLDER" if is_placeholder else "SET"
                report.append(f"  [{status:11s}] {key}")

# Check what app.py reads
env_reads = re.findall(r"os\.getenv\('(\w+)'", app_content)
report.append(f"\n  app.py reads these env vars: {', '.join(set(env_reads))}")

# Check mismatch
env_keys = set()
with open(env_path, 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            env_keys.add(line.split('=')[0].strip())
            
missing_in_env = set(env_reads) - env_keys
report.append(f"  Missing in .env (app.py needs): {missing_in_env or 'None'}")

# 4. Route analysis
section("4. ROUTE FILES ANALYSIS")
routes_dir = os.path.join(BACKEND_DIR, "routes")
for f in sorted(os.listdir(routes_dir)):
    if f.endswith('.py') and not f.startswith('__'):
        fpath = os.path.join(routes_dir, f)
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as fh:
            content = fh.read()
        
        bp_match = re.search(r"Blueprint\('(\w+)',.*?url_prefix='([^']*)'", content)
        bp_name = bp_match.group(1) if bp_match else "UNKNOWN"
        bp_prefix = bp_match.group(2) if bp_match else "UNKNOWN"
        
        routes = re.findall(r"@\w+\.route\('([^']+)'.*?methods=\[([^\]]+)\]", content)
        
        is_used = any(f.replace('.py','') in line or bp_name in line for line in app_content.split('\n'))
        status = "USED" if is_used else "UNUSED"
        
        report.append(f"\n  [{status}] {f}")
        report.append(f"    Blueprint: {bp_name}, Prefix: {bp_prefix}")
        report.append(f"    Routes ({len(routes)}):")
        for path, methods in routes[:5]:
            report.append(f"      {methods.strip()} {bp_prefix}{path}")
        if len(routes) > 5:
            report.append(f"      ... and {len(routes)-5} more")

# 5. Database check
section("5. DATABASE TABLES")
try:
    import MySQLdb
    import MySQLdb.cursors
    conn = MySQLdb.connect(host='localhost', user='root', password='sandeep@7981', db='SmartFarmingDB')
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [t[0] for t in cursor.fetchall()]
    for t in sorted(tables):
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        count = cursor.fetchone()[0]
        report.append(f"  {t:35s} {count:>6} rows")
    
    # Check for required tables
    required = ['farmers', 'buyers', 'admins', 'products', 'orders', 'cart', 
                'payments', 'buyer_reviews', 'notifications', 'conversations', 'messages']
    missing = [t for t in required if t not in tables]
    report.append(f"\n  Missing required tables: {missing or 'None'}")
    conn.close()
except Exception as e:
    report.append(f"  DB ERROR: {e}")

# 6. Frontend analysis
section("6. FRONTEND ANALYSIS")
api_path = os.path.join(FRONTEND_DIR, "src", "services", "api.js")
if os.path.exists(api_path):
    with open(api_path, 'r') as f:
        api_content = f.read()
    
    base_url = re.search(r"API_BASE_URL.*?'([^']+)'", api_content)
    report.append(f"  Base URL: {base_url.group(1) if base_url else 'NOT FOUND'}")
    
    endpoints = re.findall(r"apiClient\.(get|post|put|delete)\('([^']+)'", api_content)
    report.append(f"\n  Frontend API calls ({len(endpoints)}):")
    for method, path in endpoints:
        report.append(f"    {method.upper():6s} {path}")

# 7. Frontend pages
pages_dir = os.path.join(FRONTEND_DIR, "src", "pages")
if os.path.exists(pages_dir):
    report.append(f"\n  Pages:")
    for f in sorted(os.listdir(pages_dir)):
        if f.endswith('.js'):
            size = os.path.getsize(os.path.join(pages_dir, f))
            report.append(f"    {f:30s} {size:>8,} bytes")

# 8. Frontend components
comp_dir = os.path.join(FRONTEND_DIR, "src", "components")
if os.path.exists(comp_dir):
    report.append(f"\n  Components:")
    for f in sorted(os.listdir(comp_dir)):
        if f.endswith('.js'):
            size = os.path.getsize(os.path.join(comp_dir, f))
            report.append(f"    {f:30s} {size:>8,} bytes")

# 9. Package.json dependencies
pkg_path = os.path.join(FRONTEND_DIR, "package.json")
if os.path.exists(pkg_path):
    import json
    with open(pkg_path, 'r') as f:
        pkg = json.load(f)
    report.append(f"\n  Dependencies:")
    for dep, ver in sorted(pkg.get('dependencies', {}).items()):
        report.append(f"    {dep:30s} {ver}")

# Print report
print('\n'.join(report))
