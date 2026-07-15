"""
End-to-end test: login to EduPilot and call /chat/send
to see exactly what the AI returns from the running Flask app.
"""
import urllib.request, urllib.parse, json, http.cookiejar

BASE = 'http://localhost:5000'

# Setup cookie jar so session persists
cjar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cjar))

print("=== EduPilot Live Chat Test ===")
print()

# ── 1. Get CSRF token from login page ───────────────────────
try:
    with opener.open(f'{BASE}/auth/login', timeout=5) as r:
        html = r.read().decode()
    # Extract csrf token
    csrf = ''
    for line in html.splitlines():
        if 'csrf_token' in line and 'value=' in line:
            import re
            m = re.search(r'value="([^"]+)"', line)
            if m:
                csrf = m.group(1)
                break
    print(f"[1] Login page loaded, CSRF: {'found' if csrf else 'NOT FOUND'}")
except Exception as e:
    print(f"[1] FAIL: {e}")
    exit()

# ── 2. Login ─────────────────────────────────────────────────
try:
    data = urllib.parse.urlencode({
        'csrf_token': csrf,
        'email': 'admin@edupilot.ai',
        'password': 'Admin@123!'
    }).encode()
    req = urllib.request.Request(
        f'{BASE}/auth/login',
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded',
                 'Referer': f'{BASE}/auth/login'}
    )
    with opener.open(req, timeout=5) as r:
        status = r.status
        url = r.url
    print(f"[2] Login: HTTP {status}, redirected to: {url}")
    logged_in = '/dashboard' in url or url == f'{BASE}/'
    if not logged_in:
        print("    WARNING: May not be logged in - check credentials")
except Exception as e:
    print(f"[2] Login FAIL: {e}")
    exit()

# ── 3. Call /chat/send ────────────────────────────────────────
try:
    payload = json.dumps({"message": "Hello Aria! Are you working?"}).encode()
    req = urllib.request.Request(
        f'{BASE}/chat/send',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    )
    with opener.open(req, timeout=60) as r:
        resp_data = json.loads(r.read())

    print()
    print(f"[3] /chat/send response:")
    print(f"    Keys: {list(resp_data.keys())}")

    if 'response' in resp_data:
        print()
        print("SUCCESS! Aria replied:")
        print("-" * 40)
        print(resp_data['response'])
        print("-" * 40)
    elif 'error' in resp_data:
        print(f"    ERROR from server: {resp_data['error']}")
    else:
        print(f"    Full response: {resp_data}")

except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"[3] HTTP {e.code}: {body[:500]}")
except Exception as e:
    print(f"[3] FAIL: {e}")
