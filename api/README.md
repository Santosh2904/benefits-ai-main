# Benefits AI FastAPI

Remember to cd into this directory

## Quickstart

### Run API Locally:
```
uvicorn app:app --reload
```

### Run Frontend Image Upload Locally:
```
open test/upload_image.html
```

## Connection Details

### Request
Type: HTTP POST
```
url: http://18.235.248.248:8000/id-extract/
{'file': [IMAGE_BYTES]}
```
Sample CURL Request:
```
curl -X POST \
  -F "file=@/dummy_image.jpg" \
  http://18.235.248.248:8000/id-extract/

```

### Endpoints
Localhost at port 8000:
```
http://127.0.0.1:8000/id-extract/
```
Hosted Service in EC2: 
```
http://18.235.248.248:8000/id-extract/
```

## Deployment
### Setup
Setup Script: setup.sh
### Environment Variables
export AWS_ACCESS_KEY_ID="your_access_key_id_here"
export AWS_SECRET_ACCESS_KEY="your_secret_access_key_here"
export AWS_SESSION_TOKEN="your_session_token_here"  # Optional
export AWS_DEFAULT_REGION="your_default_region_here"
export OPENAI_API_KEY="your_open_ai_api_key_here"