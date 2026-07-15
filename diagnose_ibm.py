"""IBM Cloud Diagnostics Script for EduPilot"""
import os, json, sys
import urllib.request, urllib.parse
from dotenv import load_dotenv

load_dotenv()

api_key    = os.getenv('IBM_API_KEY', '')
project_id = os.getenv('IBM_PROJECT_ID', '')
region     = os.getenv('IBM_REGION', 'us-south')

print("=" * 55)
print("  IBM Cloud + Watsonx.ai Diagnostics")
print("=" * 55)
print(f"  API Key    : {api_key[:12]}...{api_key[-6:] if len(api_key) > 18 else '(short?)'}")
print(f"  Project ID : {project_id}")
print(f"  Region     : {region}")
print(f"  WML URL    : https://{region}.ml.cloud.ibm.com")
print()

# ─── Step 1: Validate API Key via IAM ───────────────────────
print("[1] Testing API Key via IBM IAM...")
token = None
try:
    data = urllib.parse.urlencode({
        'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
        'apikey': api_key
    }).encode()
    req = urllib.request.Request(
        'https://iam.cloud.ibm.com/identity/token',
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        td = json.loads(r.read())
        token = td.get('access_token', '')
        exp   = td.get('expires_in', 0) // 60
        print(f"    PASS  API Key is VALID  (token expires in {exp} min)")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"    FAIL  API Key invalid: HTTP {e.code}")
    print(f"          {body[:300]}")
    sys.exit(1)
except Exception as e:
    print(f"    FAIL  {e}")
    sys.exit(1)

print()

# ─── Step 2: Validate Project ───────────────────────────────
print("[2] Looking up Watsonx Project...")
try:
    req = urllib.request.Request(
        f'https://api.dataplatform.cloud.ibm.com/v2/projects/{project_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        proj = json.loads(r.read())
    ent     = proj.get('entity', {})
    name    = ent.get('name', 'Unknown')
    compute = ent.get('compute', [])

    print(f"    PASS  Project found: \"{name}\"")
    print(f"          Linked compute services: {len(compute)}")

    wml_linked = False
    for svc in compute:
        stype = svc.get('type', '')
        sname = svc.get('name', '')
        print(f"          - {sname}  [{stype}]")
        if 'machine_learning' in stype.lower() or 'wml' in stype.lower():
            wml_linked = True

    if wml_linked:
        print("    PASS  Watson Machine Learning service IS linked")
    else:
        print("    FAIL  NO Watson Machine Learning service linked!")
        print()
        print("  *** FIX REQUIRED ***")
        print("  Your project needs a WML service instance.")
        print("  See the fix steps below.")

except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"    FAIL  Project lookup failed: HTTP {e.code}")
    print(f"          {body[:300]}")
except Exception as e:
    print(f"    FAIL  {e}")

print()

# ─── Step 3: Try direct model call ──────────────────────────
print("[3] Testing Watsonx.ai model endpoint directly...")
model_id = os.getenv('WATSONX_MODEL_ID', 'ibm/granite-3-8b-instruct')
print(f"    Using model: {model_id}")
try:
    payload = json.dumps({
        "model_id": model_id,
        "input": "Reply with exactly: EduPilot connection OK",
        "parameters": {"max_new_tokens": 20},
        "project_id": project_id
    }).encode()

    req = urllib.request.Request(
        f'https://{region}.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29',
        data=payload,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type':  'application/json'
        }
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read())
    text = result.get('results', [{}])[0].get('generated_text', '').strip()
    print(f"    PASS  Model responded: \"{text}\"")
    print()
    print("=" * 55)
    print("  RESULT: Watsonx.ai is FULLY CONNECTED!")
    print("=" * 55)

except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"    FAIL  HTTP {e.code}")
    err = json.loads(body) if body.startswith('{') else {}
    for er in err.get('errors', [{}]):
        print(f"          Code    : {er.get('code','')}")
        print(f"          Message : {er.get('message','')}")
    print()
    print("=" * 55)
    print("  RESULT: Watsonx.ai NOT connected")
    print("  ROOT CAUSE: See error above")
    print("=" * 55)
except Exception as e:
    print(f"    FAIL  {e}")
