"""Quick test: simulates exactly what the Flask app does at runtime"""
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get('IBM_API_KEY', '')
project_id = os.environ.get('IBM_PROJECT_ID', '')
region = os.environ.get('IBM_REGION', 'us-south')
model_id = os.environ.get('WATSONX_MODEL_ID', 'ibm/granite-3-8b-instruct')

print(f"API KEY    : {'SET (' + api_key[:8] + '...)' if api_key else 'EMPTY'}")
print(f"PROJECT ID : {'SET (' + project_id[:8] + '...)' if project_id else 'EMPTY'}")
print(f"REGION     : {region}")
print(f"MODEL ID   : {model_id}")
print()

# Simulate WatsonxClient init
guard = api_key and project_id and api_key != 'your-ibm-cloud-api-key-here'
print(f"Will _initialize(): {guard}")
print()

if guard:
    try:
        from ibm_watsonx_ai import APIClient, Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

        url = f"https://{region}.ml.cloud.ibm.com"
        credentials = Credentials(url=url, api_key=api_key)
        client = APIClient(credentials)

        model = ModelInference(
            model_id=model_id,
            api_client=client,
            project_id=project_id,
            params={
                GenParams.MAX_NEW_TOKENS: 100,
                GenParams.TEMPERATURE: 0.7,
            }
        )
        print("ModelInference created OK")

        # Test actual chat
        response = model.chat(messages=[
            {"role": "user", "content": "Say: Aria is online and ready!"}
        ])
        print(f"Response: {response}")

        if response and 'choices' in response:
            text = response['choices'][0]['message']['content']
            print(f"\nSUCCESS: {text}")
        elif response and 'results' in response:
            text = response['results'][0].get('generated_text', '')
            print(f"\nSUCCESS (results): {text}")
        else:
            print(f"\nUnexpected structure: {type(response)}")

    except Exception as e:
        print(f"INIT FAILED: {e}")
