# 🚀 Coupon Finder Setup Guide

## Quick Start (5 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python src/server.py
```

### 3. Connect MCP Inspector
```bash
npx @modelcontextprotocol/inspector
```
Open http://localhost:3000 and connect to `http://localhost:8000/mcp`

### 4. Test with Demo
Run `demo_coupon_detection_workflow(0)` to see it work!

## Google Sheets Integration Setup

### Step 1: Google Cloud Console Setup

1. **Create/Select Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable APIs**
   - Navigate to "APIs & Services" > "Library"
   - Search and enable "Google Sheets API"
   - Search and enable "Google Drive API"

3. **Create Service Account**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Name it "coupon-finder-service"
   - Skip role assignment (click "Continue")
   - Click "Done"

4. **Generate Key File**
   - Click on your new service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create New Key"
   - Choose "JSON" format
   - Download the file (keep it secure!)

### Step 2: Google Sheets Setup

1. **Create Your Tracking Sheet**
   - Go to [Google Sheets](https://sheets.google.com)
   - Create a new sheet named "Coupon Tracker"

2. **Share with Service Account**
   - Open your credentials JSON file
   - Copy the "client_email" value
   - Share your sheet with this email address
   - Give "Editor" permissions

### Step 3: Configure in MCP

Use the `setup_sheets_integration` tool:

```python
setup_sheets_integration(
    credentials_json='PASTE_YOUR_JSON_HERE',
    sheet_name="Coupon Tracker"
)
```

## Email Client Integration

### Gmail Filters (Automatic Processing)

1. **Create Filter**
   - Gmail Settings > Filters and Blocked Addresses
   - Create new filter with criteria:
     - From: contains "deals" OR "promo" OR "offers"
     - Subject: contains "coupon" OR "discount" OR "% off"

2. **Filter Actions**
   - Apply label: "Coupons/Detected"
   - Forward to: your-coupon-processor@domain.com
   - Never send to spam

### Outlook Rules

1. **Create Rule**
   - File > Manage Rules & Alerts
   - New Rule > Apply rule on messages I receive

2. **Conditions**
   - Subject contains: "coupon", "promo", "discount"
   - From contains: "deals", "offers", "sale"

3. **Actions**
   - Move to folder: "Coupons"
   - Forward to: processing address

## Advanced Configuration

### Custom Regex Patterns

Add your own coupon patterns in `coupon_detector.py`:

```python
# Add to coupon_patterns list
r'\b[A-Z]{2}SAVE\d{2}\b',  # Pattern: ABSAVE20
r'\bSTORE\d{4}OFF\b',      # Pattern: STORE2024OFF
```

### Environment Variables

Set these for production:
```bash
export GOOGLE_SHEETS_CREDS="path/to/credentials.json"
export DEFAULT_SHEET_NAME="Production Coupon Tracker"
export LOG_LEVEL="INFO"
```

### Confidence Thresholds

Adjust detection sensitivity:
```python
# In coupon_detector.py
MIN_CONFIDENCE = 0.6  # Only accept high-confidence codes
MAX_CODE_LENGTH = 12  # Shorter codes only
```

## Troubleshooting

### Common Issues

**1. "No coupons detected" for obvious promotional emails**
- Check if keywords are present: `is_promotional_email(subject, body)`
- Verify regex patterns match your code format
- Lower confidence threshold temporarily

**2. Google Sheets authentication failed**
- Verify service account email has sheet access
- Check JSON credentials are valid
- Ensure APIs are enabled in Google Cloud

**3. Too many false positives**
- Increase confidence threshold
- Add problematic words to `false_positives` set
- Refine regex patterns

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Email Patterns

Use built-in demo emails to test changes:
```python
demo_emails = create_demo_promotional_emails()
for i, email in enumerate(demo_emails["demo_emails"]):
    result = detect_coupons_in_email(
        email["subject"], 
        email["body"], 
        email["sender"]
    )
    print(f"Email {i}: {result}")
```

## Production Deployment

### Render Deployment

1. Fork the repository
2. Connect to Render
3. Environment variables:
   - `GOOGLE_SHEETS_CREDS`: Base64 encoded JSON
   - `PORT`: 8000 (auto-set)

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
EXPOSE 8000

CMD ["python", "src/server.py"]
```

### Security Considerations

- **Never commit credentials** to version control
- **Use environment variables** for sensitive data
- **Rotate service account keys** regularly
- **Monitor API usage** in Google Cloud Console
- **Set up alerts** for unusual activity

## Performance Tips

### Batch Processing
Process multiple emails efficiently:
```python
emails = get_inbox_emails()
promotional_emails = [e for e in emails if is_promotional_email(e.subject, e.body)]

# Process in batches
for email in promotional_emails:
    log_coupons_to_sheets(email.subject, email.body, email.sender)
```

### Caching Results
Avoid reprocessing the same emails:
```python
# Store processed email IDs
processed_emails = set()

if email_id not in processed_emails:
    result = detect_coupons_in_email(subject, body, sender)
    processed_emails.add(email_id)
```

### Rate Limiting
Google Sheets API has limits:
- 300 requests per minute per project
- 100 requests per 100 seconds per user

Implement delays for bulk processing:
```python
import time
time.sleep(0.2)  # 200ms delay between requests
```

## Next Steps

1. **Test thoroughly** with your real emails
2. **Set up monitoring** for the service
3. **Create backup** of your Google Sheet
4. **Document your customizations**
5. **Share your success** with the community!

Need help? Check the troubleshooting section or create an issue in the repository.