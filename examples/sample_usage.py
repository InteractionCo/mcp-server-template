#!/usr/bin/env python3
"""
Sample usage examples for the Coupon Finder MCP Server.
These examples show how to use the various tools effectively.
"""

import json
from datetime import datetime

# Example 1: Basic Coupon Detection
def example_basic_detection():
    """Demonstrate basic coupon detection from email content."""
    
    print("=== Example 1: Basic Coupon Detection ===")
    
    # Sample promotional email
    subject = "🎉 Exclusive 25% OFF - Use Code SAVE25NOW"
    body = """
    Hey there!
    
    We're excited to offer you an exclusive 25% discount!
    Use promo code: SAVE25NOW at checkout
    Valid until midnight tonight only!
    
    Shop now and save big!
    """
    sender = "deals@fashionstore.com"
    
    # This would be called via MCP
    print(f"Subject: {subject}")
    print(f"Sender: {sender}")
    print(f"Expected to find: SAVE25NOW")
    print("Call: detect_coupons_in_email(subject, body, sender)")
    print("Expected result: High confidence detection of SAVE25NOW")
    print()

def example_promotional_check():
    """Demonstrate quick promotional email detection."""
    
    print("=== Example 2: Promotional Email Check ===")
    
    # Test different email types
    emails = [
        {
            "subject": "Your order has shipped",
            "body": "Thank you for your purchase. Tracking: 123456789",
            "expected": False
        },
        {
            "subject": "Flash Sale - 50% Off Everything!",
            "body": "Limited time offer with huge discounts",
            "expected": True
        },
        {
            "subject": "Newsletter - Weekly Updates",
            "body": "Here are this week's news and updates",
            "expected": False
        }
    ]
    
    for i, email in enumerate(emails):
        print(f"Email {i+1}:")
        print(f"  Subject: {email['subject']}")
        print(f"  Expected promotional: {email['expected']}")
        print(f"  Call: is_promotional_email(subject, body)")
        print()

def example_sheets_integration():
    """Demonstrate Google Sheets integration workflow."""
    
    print("=== Example 3: Google Sheets Integration ===")
    
    # Sample credentials structure (DO NOT use real credentials here)
    sample_creds = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
        "client_email": "service-account@project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    
    print("Step 1: Setup Google Sheets integration")
    print("Call: setup_sheets_integration(credentials_json, 'My Coupon Tracker')")
    print(f"Credentials structure: {json.dumps(sample_creds, indent=2)}")
    print()
    
    print("Step 2: Log coupons from email")
    subject = "Welcome Gift - 20% Off Your First Order!"
    body = "Use code WELCOME20 at checkout for 20% off"
    sender = "hello@store.com"
    
    print(f"Email to process:")
    print(f"  Subject: {subject}")
    print(f"  Sender: {sender}")
    print("Call: log_coupons_to_sheets(subject, body, sender)")
    print()
    
    print("Step 3: Update coupon status after use")
    print("Call: update_coupon_status('WELCOME20', 'Used', 'Worked great!')")
    print()

def example_demo_workflow():
    """Demonstrate the complete demo workflow."""
    
    print("=== Example 4: Demo Workflow ===")
    
    print("Step 1: Get demo emails")
    print("Call: create_demo_promotional_emails()")
    print("Returns: 5 realistic promotional emails with various coupon patterns")
    print()
    
    print("Step 2: Run complete workflow demo")
    print("Call: demo_coupon_detection_workflow(0)  # Use first demo email")
    print("Returns:")
    print("  - Promotional check results")
    print("  - Detected coupon codes with confidence")
    print("  - Google Sheets integration status")
    print("  - Accuracy assessment")
    print()

def example_batch_processing():
    """Example of processing multiple emails efficiently."""
    
    print("=== Example 5: Batch Processing ===")
    
    # Simulated inbox emails
    inbox_emails = [
        {
            "id": "email_1",
            "subject": "Your receipt from Store ABC",
            "body": "Thank you for your purchase...",
            "sender": "receipts@store.com"
        },
        {
            "id": "email_2", 
            "subject": "Flash Sale - 40% Off Today Only!",
            "body": "Use code FLASH40 for huge savings...",
            "sender": "deals@fashion.com"
        },
        {
            "id": "email_3",
            "subject": "Weekend Special - Free Shipping",
            "body": "Get free shipping with FREESHIP2024...",
            "sender": "offers@electronics.com"
        }
    ]
    
    print("Processing strategy:")
    print("1. First, quickly check which emails are promotional")
    print("2. Then process only promotional emails for coupons")
    print("3. Log found coupons to sheets")
    print()
    
    for email in inbox_emails:
        print(f"Email ID: {email['id']}")
        print(f"  Subject: {email['subject']}")
        print(f"  Step 1: is_promotional_email(subject, body)")
        print(f"  Step 2: If promotional, detect_coupons_in_email(...)")
        print(f"  Step 3: If coupons found, log_coupons_to_sheets(...)")
        print()

def example_error_handling():
    """Demonstrate proper error handling."""
    
    print("=== Example 6: Error Handling ===")
    
    scenarios = [
        {
            "case": "Empty email content",
            "subject": "",
            "body": "",
            "expected": "No promotional content detected"
        },
        {
            "case": "Malformed text",
            "subject": "ÿÿÿ ¿¿¿ ™™™",
            "body": "ßßß ÷÷÷ ±±±",
            "expected": "Graceful handling of special characters"
        },
        {
            "case": "Very long email",
            "subject": "Sale! " * 1000,
            "body": "Discount " * 10000,
            "expected": "Efficient processing of large content"
        }
    ]
    
    for scenario in scenarios:
        print(f"Test case: {scenario['case']}")
        print(f"Expected: {scenario['expected']}")
        print()

def example_customization():
    """Show how to customize the system for specific needs."""
    
    print("=== Example 7: Customization Examples ===")
    
    print("Custom regex patterns for specific stores:")
    custom_patterns = [
        r'\bAMAZON\d{4,8}\b',      # Amazon-style codes
        r'\bEBAY[A-Z0-9]{4,8}\b',  # eBay-style codes
        r'\b\d{4}-\d{4}-\d{4}\b',  # Hyphenated codes
    ]
    
    print("Add these patterns to coupon_detector.py:")
    for pattern in custom_patterns:
        print(f"  {pattern}")
    print()
    
    print("Custom false positives filter:")
    custom_false_positives = [
        "WALMART", "TARGET", "BESTBUY",  # Store names
        "MONDAY", "TUESDAY", "WEDNESDAY",  # Days
        "JANUARY", "FEBRUARY", "MARCH"     # Months
    ]
    
    print("Add these to false_positives set:")
    for fp in custom_false_positives:
        print(f"  {fp}")
    print()

def example_monitoring():
    """Demonstrate monitoring and statistics."""
    
    print("=== Example 8: Monitoring & Statistics ===")
    
    print("Regular monitoring calls:")
    print("1. get_coupon_statistics() - Overall coupon tracking stats")
    print("2. get_server_info() - Server status and capabilities")
    print()
    
    print("Sample statistics output:")
    sample_stats = {
        "success": True,
        "total_coupons": 47,
        "status_breakdown": {
            "New": 23,
            "Used": 18,
            "Expired": 6
        },
        "average_confidence": 0.82,
        "sheet_url": "https://docs.google.com/spreadsheets/d/abc123..."
    }
    
    print(json.dumps(sample_stats, indent=2))
    print()

if __name__ == "__main__":
    """Run all examples to see the complete system functionality."""
    
    print("🎯 Coupon Finder MCP Server - Usage Examples")
    print("=" * 50)
    print()
    
    example_basic_detection()
    example_promotional_check() 
    example_sheets_integration()
    example_demo_workflow()
    example_batch_processing()
    example_error_handling()
    example_customization()
    example_monitoring()
    
    print("🎉 All examples completed!")
    print("\nNext steps:")
    print("1. Start the MCP server: python src/server.py")
    print("2. Connect MCP inspector: npx @modelcontextprotocol/inspector")
    print("3. Try the demo: demo_coupon_detection_workflow(0)")
    print("4. Set up Google Sheets integration")
    print("5. Process your real emails!")