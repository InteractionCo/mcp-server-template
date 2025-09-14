# 🎯 Coupon Finder MCP Server

**Never miss a discount again!** An intelligent MCP automation that detects promo codes and coupons from incoming emails and organizes them for easy use.

*Designed for the "Most Practical MCP Automation" prize - this tool saves you time and money by automatically finding and tracking coupon codes in your email.*

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/InteractionCo/mcp-server-template)

## 🚀 What It Does

The Coupon Finder automatically:

1. **🔍 Detects Promotional Emails** - Scans for keywords like "coupon," "promo code," "discount," "% off," "deal"
2. **🎯 Extracts Coupon Codes** - Uses advanced regex patterns to find alphanumeric codes (5-15 characters)
3. **📊 Logs to Google Sheets** - Saves codes with metadata for easy tracking and organization  
4. **📋 Organizes Your Inbox** - Provides recommendations for email labeling and forwarding
5. **🎮 Demo Mode** - Test with realistic sample promotional emails

## 🏆 Why This Wins "Most Practical MCP Automation"

- **💰 Immediate Value**: Never lose money by missing discount codes
- **⚡ Fast to Build**: Complete automation in under a day
- **🔧 Easy to Hack**: Modular design for customization
- **📱 Real-World Useful**: Solves an everyday problem everyone has
- **🎯 Highly Accurate**: Advanced pattern matching with confidence scoring

## 🛠️ Setup & Installation

### Local Development

```bash
# Clone and setup
git clone <your-repo-url>
cd coupon-finder
conda create -n coupon-finder python=3.13
conda activate coupon-finder
pip install -r requirements.txt

# Start the server
python src/server.py
```

### Connect via MCP Inspector

```bash
# In another terminal
npx @modelcontextprotocol/inspector
```

Open http://localhost:3000 and connect to `http://localhost:8000/mcp` using "Streamable HTTP" transport.

## 📋 Available Tools

### Core Detection Tools

#### `detect_coupons_in_email`
Analyzes email content for promotional codes and coupons.
```python
# Example usage
result = detect_coupons_in_email(
    email_subject="🎉 25% OFF with code SAVE25NOW!",
    email_body="Use promo code SAVE25NOW at checkout...",
    sender_email="deals@store.com"
)
```

#### `is_promotional_email`
Quick check if an email contains promotional content.
```python
promo_check = is_promotional_email(
    email_subject="Flash Sale Tonight Only!",
    email_body="Limited time discount inside..."
)
```

### Google Sheets Integration

#### `setup_sheets_integration`
Configure Google Sheets for coupon logging.
```python
setup_sheets_integration(
    credentials_json='{"type": "service_account", ...}',
    sheet_name="My Coupon Tracker"
)
```

#### `log_coupons_to_sheets`
Automatically detect and log coupons to your tracking sheet.
```python
log_coupons_to_sheets(
    email_subject="Your discount code inside!",
    email_body="Use WELCOME20 for 20% off...",
    sender_email="hello@store.com"
)
```

#### `update_coupon_status`
Mark coupons as used, expired, etc.
```python
update_coupon_status(
    coupon_code="SAVE25NOW",
    status="Used",
    notes="Worked great on electronics purchase!"
)
```

### Demo & Testing Tools

#### `create_demo_promotional_emails`
Generate realistic sample promotional emails for testing.

#### `demo_coupon_detection_workflow`
Run complete workflow demo with sample data.
```python
demo_result = demo_coupon_detection_workflow(demo_email_index=0)
```

#### `get_coupon_statistics`
View statistics about your tracked coupons.

#### `get_server_info`
Get detailed server information and setup status.

## 🎮 Quick Demo

Try this workflow to see the system in action:

1. **Get Demo Emails**: `create_demo_promotional_emails()`
2. **Run Detection**: `demo_coupon_detection_workflow(0)`
3. **Setup Sheets**: `setup_sheets_integration(credentials, "Demo Tracker")`
4. **Log Coupons**: `log_coupons_to_sheets(subject, body, sender)`
5. **Check Stats**: `get_coupon_statistics()`

## 🔧 Google Sheets Setup

### 1. Create Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Enable Google Sheets API
4. Create service account credentials
5. Download JSON key file

### 2. Share Sheet Access
1. Copy the service account email from the JSON
2. Share your Google Sheet with this email address
3. Give "Editor" permissions

### 3. Configure in MCP
Use the `setup_sheets_integration` tool with your credentials JSON.

## 🎯 Supported Coupon Patterns

The system detects various coupon code formats:

- **Standard Codes**: `SAVE25NOW`, `DISCOUNT123`, `PROMO456`
- **Percentage Codes**: `20OFF`, `SAVE30PERCENT`, `GET25PCT`
- **Seasonal Codes**: `SUMMER2024`, `BLACKFRIDAY`, `HOLIDAY25`
- **Free Shipping**: `FREESHIP`, `SHIPFREE99`, `NOSHIPCOST`
- **Welcome Codes**: `WELCOME20`, `NEW15`, `HELLO10`
- **Brand Patterns**: `ABC1234`, `TECH789`, `FASHION2024`

## 📊 Features & Accuracy

### Advanced Detection
- **40+ Regex Patterns** for comprehensive code matching
- **Confidence Scoring** (0.0-1.0) for each detected code
- **Context Analysis** to reduce false positives
- **Duplicate Prevention** when logging to sheets

### Smart Filtering
- **False Positive Filtering** (excludes common words like "UNSUBSCRIBE")
- **Length Validation** (4-15 character codes)
- **Format Validation** (mixed alphanumeric preferred)
- **Keyword Correlation** (codes must appear with promotional keywords)

### Practical Organization  
- **Google Sheets Logging** with timestamps and metadata
- **Status Tracking** (New, Used, Expired)
- **Usage Notes** for each coupon
- **Statistics Dashboard** for tracking savings

## 🚀 Deployment Options

### Option 1: One-Click Deploy
Click the "Deploy to Render" button above.

### Option 2: Manual Deployment
1. Fork this repository
2. Connect GitHub to Render
3. Create new Web Service
4. Render detects `render.yaml` automatically

Your server: `https://your-service-name.onrender.com/mcp`

## 🎪 Real-World Usage Examples

### Email Automation Integration
Use with email triggers to process incoming messages:
```python
# When new email arrives
if is_promotional_email(subject, body):
    log_coupons_to_sheets(subject, body, sender)
    # Move to "Coupons" folder
    # Or forward to coupon tracking email
```

### Batch Processing
Process multiple emails at once:
```python
for email in inbox:
    if is_promotional_email(email.subject, email.body):
        result = log_coupons_to_sheets(
            email.subject, 
            email.body, 
            email.sender
        )
```

### Shopping Assistant
Check for available coupons before purchases:
```python
stats = get_coupon_statistics()
# Show available unused coupons by store/brand
```

## 🔍 Architecture Overview

```
Email Input → Keyword Detection → Code Extraction → Confidence Scoring → Google Sheets Logging
     ↓              ↓                    ↓                 ↓                    ↓
Promotional    Pattern Matching    Regex Processing    False Positive      Organized Tracking
   Check        (40+ patterns)     + Context Analysis     Filtering         + Status Updates
```

## 🎯 Competition Advantages

1. **Practical Impact**: Solves real money-saving problem
2. **Immediate ROI**: Users see value from first coupon found  
3. **Scalable**: Handles hundreds of emails efficiently
4. **Extensible**: Easy to add new patterns and features
5. **User-Friendly**: Simple setup, powerful automation

## 🤝 Contributing

This project is designed to be easily hackable! Add your own:
- Coupon code patterns for specific stores
- Integration with other services (Notion, Airtable, etc.)
- Email client plugins
- Mobile app connections

## 📄 License

MIT License - Build amazing things with this code!

---

**💡 Pro Tip**: Set up email filters to automatically forward promotional emails to this system, and you'll never miss a discount again!
