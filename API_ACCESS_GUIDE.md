# API Access Guide

## For Frontend Developer

### API URL
The API is deployed at: `https://vigilore-api.onrender.com`

### Authentication
- **No API key required** - The API is currently open
- OpenAI key is already set in Render environment variables
- All endpoints are publicly accessible

### Quick Test
Test if the API is working:
```bash
curl https://vigilore-api.onrender.com/
```

Should return:
```json
{"status": "healthy", "version": "2.0.0"}
```

### CORS
- CORS is enabled for all origins (`*`)
- Your frontend can call the API from any domain
- No special headers needed

## For API Owner

### Current Setup
1. **OpenAI Key**: Set in Render environment variables (OPENAI_API_KEY)
2. **No Authentication**: API is open (fine for POC/testing)
3. **Rate Limiting**: None currently implemented

### To Test Your Deployment:

1. **Check API Health:**
   ```bash
   curl https://vigilore-api.onrender.com/
   ```

2. **Test OpenAI Key:**
   - Submit a small test audit through the API
   - Check Render logs for any OpenAI errors

3. **Monitor Usage:**
   - Check Render dashboard for request logs
   - Monitor OpenAI usage at platform.openai.com

### Security Considerations (For Production)

If you later want to add authentication:

1. **API Key Method** (Simple):
   ```python
   # Add to api_v2.py
   API_KEY = os.getenv("API_ACCESS_KEY")
   
   async def verify_api_key(api_key: str = Header(...)):
       if api_key != API_KEY:
           raise HTTPException(status_code=401)
   
   # Add to endpoints:
   @app.post("/audits", dependencies=[Depends(verify_api_key)])
   ```

2. **User Authentication** (Advanced):
   - Add user registration/login
   - Use JWT tokens
   - Track usage per user

For now, the open API is perfect for development and testing!