"""List all available IBM Granite models in your WML instance"""
import os, json, sys
import urllib.request, urllib.parse
from dotenv import load_dotenv

load_dotenv()

api_key    = os.getenv('IBM_API_KEY', '')
project_id = os.getenv('IBM_PROJECT_ID', '')
region     = os.getenv('IBM_REGION', 'us-south')

# Get IAM token
data = urllib.parse.urlencode({
    'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
    'apikey': api_key
}).encode()
req = urllib.request.Request(
    'https://iam.cloud.ibm.com/identity/token',
    data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'}
)
with urllib.request.urlopen(req, timeout=15) as r:
    token = json.loads(r.read())['access_token']

print("Available IBM Foundation Models (Granite):")
print("=" * 60)

try:
    url = f'https://{region}.ml.cloud.ibm.com/ml/v1/foundation_model_specs?version=2023-05-29&project_id={project_id}&limit=200'
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())

    models = data.get('resources', [])
    granite_models = [m for m in models if 'granite' in m.get('model_id','').lower()]

    print(f"Total models available: {len(models)}")
    print(f"Granite models: {len(granite_models)}")
    print()

    for m in granite_models:
        mid   = m.get('model_id','')
        label = m.get('label', m.get('name',''))
        print(f"  ID    : {mid}")
        print(f"  Name  : {label}")
        print()

except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body[:500]}")
    # Try alternate: list without project_id to see if it's a scope issue
    print()
    print("Trying without project_id filter...")
    try:
        url2 = f'https://{region}.ml.cloud.ibm.com/ml/v1/foundation_model_specs?version=2023-05-29&filters=!lifecycle_withdrawn&limit=200'
        req2 = urllib.request.Request(url2, headers={'Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(req2, timeout=20) as r2:
            data2 = json.loads(r2.read())
        models2 = data2.get('resources', [])
        granite2 = [m for m in models2 if 'granite' in m.get('model_id','').lower()]
        print(f"  Found {len(granite2)} Granite models globally:")
        for m in granite2:
            print(f"  -> {m.get('model_id','')}")
    except Exception as e2:
        print(f"  Also failed: {e2}")
