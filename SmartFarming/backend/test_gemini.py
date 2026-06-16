import requests

API_KEY = 'AQ.Ab8RN6IEXR-bEe4Q3EmgD2eSYH65nSWdE9GFBA47GKNmOhKXBQ'
MODELS = ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-1.5-flash-latest']

for model in MODELS:
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}'
    payload = {
        'contents': [{'parts': [{'text': 'Say hello in one line'}]}],
        'generationConfig': {'maxOutputTokens': 50}
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        data = r.json()
        if 'candidates' in data:
            text = data['candidates'][0]['content']['parts'][0]['text']
            print(f"OK {model}: {text[:60]}")
            break
        else:
            err = data.get('error', {}).get('message', str(data)[:80])
            print(f"FAIL {model}: {err[:80]}")
    except Exception as e:
        print(f"FAIL {model}: {str(e)[:60]}")
