#!/usr/bin/env python3
"""
Coupon Finder MCP Server - Automated detection and organization of promo codes from emails.

This MCP server provides tools to:
1. Detect promotional emails and extract coupon codes
2. Log coupons to Google Sheets for easy tracking
3. Organize emails with coupon detection results
4. Demo the system with sample promotional emails

Designed for the "Most Practical MCP Automation" prize - never miss a discount again!
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastmcp import FastMCP

# Import our modules
from coupon_detector import CouponDetector, CouponCode
from sheets_integration import SheetsLogger

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("Coupon Finder MCP Server")

# Global instances (will be initialized per request as needed)
coupon_detector = CouponDetector()
sheets_logger = None

@mcp.tool(description="Analyze an email to detect promotional content and extract coupon codes")
def detect_coupons_in_email(
    email_subject: str, 
    email_body: str, 
    sender_email: str = ""
) -> Dict[str, Any]:
    """
    Main coupon detection tool. Analyzes email content for promo codes and coupons.
    
    Args:
        email_subject: The subject line of the email
        email_body: The full body content of the email
        sender_email: Optional sender email address
    
    Returns:
        Dictionary with detection results including found codes, confidence scores, and statistics
    """
    try:
        logger.info(f"Analyzing email from {sender_email}: {email_subject[:50]}...")
        
        # Detect coupons
        detected_coupons = coupon_detector.detect_coupons_in_email(
            subject=email_subject,
            body=email_body,
            sender=sender_email
        )
        
        # Get statistics
        stats = coupon_detector.get_detection_stats(detected_coupons)
        
        # Format results
        coupon_results = []
        for coupon in detected_coupons:
            coupon_results.append({
                "code": coupon.code,
                "confidence": coupon.confidence,
                "context": coupon.context,
                "keywords_found": coupon.keywords_found
            })
        
        return {
            "is_promotional": len(detected_coupons) > 0,
            "coupons_found": coupon_results,
            "total_codes": stats["total_codes"],
            "average_confidence": stats["avg_confidence"],
            "keywords_detected": stats["keywords_found"],
            "analysis_timestamp": datetime.now().isoformat(),
            "recommendation": _get_recommendation(detected_coupons)
        }
        
    except Exception as e:
        logger.error(f"Error detecting coupons: {e}")
        return {
            "error": f"Failed to analyze email: {str(e)}",
            "is_promotional": False,
            "coupons_found": []
        }

@mcp.tool(description="Check if an email appears to be promotional based on keywords")
def is_promotional_email(email_subject: str, email_body: str) -> Dict[str, Any]:
    """
    Quick check to determine if an email is promotional/marketing content.
    
    Args:
        email_subject: Email subject line
        email_body: Email body content
    
    Returns:
        Dictionary with promotional status and found keywords
    """
    try:
        is_promo = coupon_detector.is_promotional_email(email_subject, email_body)
        keywords = coupon_detector.extract_keywords(f"{email_subject} {email_body}")
        
        return {
            "is_promotional": is_promo,
            "keywords_found": keywords,
            "keyword_count": len(keywords),
            "confidence": min(len(keywords) * 0.2, 1.0),
            "recommendation": "Process for coupons" if is_promo else "No promotional content detected"
        }
        
    except Exception as e:
        logger.error(f"Error checking promotional status: {e}")
        return {
            "error": f"Failed to analyze email: {str(e)}",
            "is_promotional": False
        }

@mcp.tool(description="Set up Google Sheets integration for logging detected coupons")
def setup_sheets_integration(
    credentials_json: str, 
    sheet_name: str = "Coupon Tracker"
) -> Dict[str, Any]:
    """
    Configure Google Sheets integration for coupon logging.
    
    Args:
        credentials_json: JSON string containing Google service account credentials
        sheet_name: Name for the Google Sheet (will be created if doesn't exist)
    
    Returns:
        Setup status and sheet information
    """
    global sheets_logger
    
    try:
        sheets_logger = SheetsLogger(credentials_json, sheet_name)
        
        if sheets_logger.create_or_get_sheet():
            return {
                "success": True,
                "message": f"Google Sheets integration set up successfully",
                "sheet_name": sheet_name,
                "sheet_url": sheets_logger.get_sheet_url(),
                "status": "Ready to log coupons"
            }
        else:
            return {
                "success": False,
                "error": "Failed to create or access Google Sheet",
                "message": "Check your credentials and permissions"
            }
    
    except Exception as e:
        logger.error(f"Error setting up sheets integration: {e}")
        return {
            "success": False,
            "error": f"Setup failed: {str(e)}"
        }

@mcp.tool(description="Log detected coupons to Google Sheets for tracking")
def log_coupons_to_sheets(
    email_subject: str, 
    email_body: str, 
    sender_email: str = ""
) -> Dict[str, Any]:
    """
    Detect coupons in an email and log them to Google Sheets.
    
    Args:
        email_subject: Email subject line
        email_body: Email body content
        sender_email: Sender's email address
    
    Returns:
        Results of detection and logging process
    """
    global sheets_logger
    
    if not sheets_logger:
        return {
            "error": "Google Sheets not configured. Run setup_sheets_integration first.",
            "success": False
        }
    
    try:
        # Detect coupons first
        detected_coupons = coupon_detector.detect_coupons_in_email(
            subject=email_subject,
            body=email_body,
            sender=sender_email
        )
        
        if not detected_coupons:
            return {
                "success": True,
                "message": "No coupons detected in email",
                "coupons_logged": 0
            }
        
        # Check for existing coupons to avoid duplicates
        existing_codes = sheets_logger.get_existing_coupons()
        new_coupons = [c for c in detected_coupons if c.code not in existing_codes]
        
        if not new_coupons:
            return {
                "success": True,
                "message": "All detected coupons already exist in sheet",
                "coupons_logged": 0,
                "duplicate_codes": [c.code for c in detected_coupons]
            }
        
        # Log new coupons
        results = sheets_logger.log_multiple_coupons(new_coupons)
        
        return {
            "success": True,
            "message": f"Successfully processed {len(detected_coupons)} coupons",
            "coupons_logged": results["success"],
            "coupons_failed": results["failed"],
            "new_codes": [c.code for c in new_coupons],
            "sheet_url": sheets_logger.get_sheet_url()
        }
        
    except Exception as e:
        logger.error(f"Error logging coupons to sheets: {e}")
        return {
            "success": False,
            "error": f"Failed to log coupons: {str(e)}"
        }

@mcp.tool(description="Update the status of a coupon code (e.g., mark as used)")
def update_coupon_status(
    coupon_code: str, 
    status: str, 
    notes: str = ""
) -> Dict[str, Any]:
    """
    Update the status of a coupon in the Google Sheet.
    
    Args:
        coupon_code: The coupon code to update
        status: New status (e.g., "Used", "Expired", "Active")
        notes: Optional notes about the coupon
    
    Returns:
        Update status and confirmation
    """
    global sheets_logger
    
    if not sheets_logger:
        return {
            "error": "Google Sheets not configured. Run setup_sheets_integration first.",
            "success": False
        }
    
    try:
        used_date = datetime.now().strftime("%Y-%m-%d") if status.lower() == "used" else ""
        
        success = sheets_logger.update_coupon_status(
            coupon_code=coupon_code,
            status=status,
            used_date=used_date,
            notes=notes
        )
        
        if success:
            return {
                "success": True,
                "message": f"Updated {coupon_code} status to {status}",
                "coupon_code": coupon_code,
                "new_status": status
            }
        else:
            return {
                "success": False,
                "error": f"Could not find or update coupon {coupon_code}"
            }
            
    except Exception as e:
        logger.error(f"Error updating coupon status: {e}")
        return {
            "success": False,
            "error": f"Failed to update status: {str(e)}"
        }

@mcp.tool(description="Get statistics about logged coupons from Google Sheets")
def get_coupon_statistics() -> Dict[str, Any]:
    """
    Retrieve statistics about all logged coupons from Google Sheets.
    
    Returns:
        Statistics including total coupons, status breakdown, and sheet URL
    """
    global sheets_logger
    
    if not sheets_logger:
        return {
            "error": "Google Sheets not configured. Run setup_sheets_integration first.",
            "success": False
        }
    
    try:
        stats = sheets_logger.get_coupon_statistics()
        return {
            "success": True,
            **stats
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return {
            "success": False,
            "error": f"Failed to get statistics: {str(e)}"
        }

@mcp.tool(description="Generate demo promotional emails for testing the coupon detection system")
def create_demo_promotional_emails() -> Dict[str, List[Dict[str, str]]]:
    """
    Create sample promotional emails for demonstrating the coupon detection system.
    
    Returns:
        Collection of demo emails with various coupon code patterns
    """
    demo_emails = [
        {
            "subject": "🎉 Exclusive 25% OFF - Use Code SAVE25NOW",
            "sender": "deals@fashionstore.com",
            "body": """
            Hey there!
            
            We're excited to offer you an exclusive 25% discount on your next purchase!
            
            Use promo code: SAVE25NOW at checkout
            Valid until midnight tonight only!
            
            Shop now and save big on:
            • New arrivals
            • Best sellers
            • Seasonal items
            
            Don't miss out on this limited-time offer!
            
            Happy shopping!
            Fashion Store Team
            """,
            "expected_codes": ["SAVE25NOW"]
        },
        {
            "subject": "Free Shipping Weekend + Special Discount Inside!",
            "sender": "notifications@techdeals.com",
            "body": """
            FREE SHIPPING WEEKEND IS HERE! 🚚
            
            Plus, get an additional 15% off with code: TECH15OFF
            
            This weekend only:
            ✓ Free shipping on all orders
            ✓ Extra 15% discount with TECH15OFF
            ✓ Up to 50% off electronics
            
            Use coupon code FREESHIP2024 for free shipping (if you missed the weekend)
            
            Hurry, offer expires Sunday at 11:59 PM!
            """,
            "expected_codes": ["TECH15OFF", "FREESHIP2024"]
        },
        {
            "subject": "Your VIP Code: WELCOME20 - New Customer Special",
            "sender": "hello@beautybox.com",
            "body": """
            Welcome to Beauty Box! 💄
            
            As a new customer, you get 20% off your first order!
            Your exclusive VIP code: WELCOME20
            
            Valid on all products except gift cards.
            Enter code at checkout to apply discount.
            
            Browse our collection:
            - Skincare essentials
            - Makeup must-haves  
            - Hair care products
            
            Code expires in 7 days. Shop now!
            """,
            "expected_codes": ["WELCOME20"]
        },
        {
            "subject": "⚡ FLASH SALE: 40% OFF Everything - Code FLASH40",
            "sender": "sales@sportsgear.com",
            "body": """
            🔥 24-HOUR FLASH SALE 🔥
            
            40% OFF EVERYTHING!
            Use code: FLASH40
            
            No exclusions. No minimum purchase.
            Just use promo code FLASH40 at checkout.
            
            Sale ends in: 23 hours 45 minutes
            
            Shop categories:
            → Running gear
            → Gym equipment  
            → Outdoor sports
            → Team sports
            
            This deal won't last long!
            """,
            "expected_codes": ["FLASH40"]
        },
        {
            "subject": "Black Friday Early Access - Multiple Codes Inside!",
            "sender": "earlyaccess@megastore.com",
            "body": """
            🖤 BLACK FRIDAY EARLY ACCESS 🖤
            
            You're getting exclusive early access to our Black Friday deals!
            
            Use these codes:
            • BLACKFRIDAY30 - 30% off orders over $100
            • CYBER50 - 50% off electronics  
            • HOLIDAY25 - 25% off everything else
            • FREESHIP99 - Free shipping on $99+ orders
            
            Stack codes where applicable!
            
            Early access ends tonight at midnight.
            Public sale starts tomorrow.
            
            Shop now before everyone else!
            """,
            "expected_codes": ["BLACKFRIDAY30", "CYBER50", "HOLIDAY25", "FREESHIP99"]
        }
    ]
    
    return {
        "demo_emails": demo_emails,
        "total_emails": len(demo_emails),
        "usage_tip": "Use these with detect_coupons_in_email() or log_coupons_to_sheets() to test the system"
    }

@mcp.tool(description="Process a demo email and show complete coupon detection workflow")
def demo_coupon_detection_workflow(demo_email_index: int = 0) -> Dict[str, Any]:
    """
    Run a complete demo of the coupon detection workflow using sample emails.
    
    Args:
        demo_email_index: Index of demo email to use (0-4)
    
    Returns:
        Complete workflow results showing detection and potential logging
    """
    try:
        demo_data = create_demo_promotional_emails()
        demo_emails = demo_data["demo_emails"]
        
        if demo_email_index >= len(demo_emails):
            return {
                "error": f"Invalid demo email index. Use 0-{len(demo_emails)-1}",
                "available_emails": len(demo_emails)
            }
        
        email = demo_emails[demo_email_index]
        
        # Step 1: Check if promotional
        promo_check = is_promotional_email(email["subject"], email["body"])
        
        # Step 2: Detect coupons
        detection_result = detect_coupons_in_email(
            email["subject"], 
            email["body"], 
            email["sender"]
        )
        
        # Step 3: Simulation of sheet logging (if configured)
        sheets_status = "Not configured - run setup_sheets_integration() first"
        if sheets_logger:
            sheets_status = "Ready - would log coupons automatically"
        
        return {
            "demo_email": {
                "subject": email["subject"],
                "sender": email["sender"],
                "expected_codes": email["expected_codes"]
            },
            "step_1_promotional_check": promo_check,
            "step_2_coupon_detection": detection_result,
            "step_3_sheets_status": sheets_status,
            "workflow_summary": {
                "promotional_email": promo_check["is_promotional"],
                "codes_detected": len(detection_result.get("coupons_found", [])),
                "expected_codes": len(email["expected_codes"]),
                "detection_accuracy": _calculate_accuracy(
                    detection_result.get("coupons_found", []), 
                    email["expected_codes"]
                )
            }
        }
        
    except Exception as e:
        logger.error(f"Error in demo workflow: {e}")
        return {
            "error": f"Demo failed: {str(e)}"
        }

@mcp.tool(description="Get comprehensive information about the Coupon Finder MCP server")
def get_server_info() -> Dict[str, Any]:
    """Get detailed information about the Coupon Finder MCP server and its capabilities."""
    return {
        "server_name": "Coupon Finder MCP Server",
        "version": "1.0.0",
        "description": "Automated detection and organization of promo codes from emails",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "capabilities": [
            "Email content analysis for promotional keywords",
            "Advanced regex-based coupon code extraction",
            "Google Sheets integration for coupon tracking",
            "Email organization and labeling recommendations",
            "Demo system with sample promotional emails",
            "Confidence scoring for detected codes"
        ],
        "supported_patterns": [
            "Standard alphanumeric codes (5-15 chars)",
            "Percentage-based codes (20OFF, SAVE30, etc.)",
            "Holiday/seasonal codes (SUMMER2024, BLACKFRIDAY, etc.)",
            "Free shipping codes (FREESHIP, SHIPFREE, etc.)",
            "Welcome/new customer codes (WELCOME20, NEW15, etc.)",
            "Brand-specific patterns",
            "Quoted or bracketed codes"
        ],
        "integration_status": {
            "google_sheets": "Available" if sheets_logger else "Not configured",
            "coupon_detector": "Active",
            "demo_system": "Available"
        },
        "setup_instructions": {
            "1": "Use setup_sheets_integration() with Google service account credentials",
            "2": "Test with demo emails using demo_coupon_detection_workflow()",
            "3": "Process real emails with detect_coupons_in_email()",
            "4": "Log coupons automatically with log_coupons_to_sheets()"
        }
    }

# Helper functions
def _get_recommendation(coupons: List[CouponCode]) -> str:
    """Generate recommendation based on detected coupons."""
    if not coupons:
        return "No coupons detected - email may not be promotional"
    
    high_confidence = [c for c in coupons if c.confidence >= 0.8]
    medium_confidence = [c for c in coupons if 0.5 <= c.confidence < 0.8]
    
    if high_confidence:
        return f"High confidence: {len(high_confidence)} likely coupon codes detected - recommend saving to coupons folder"
    elif medium_confidence:
        return f"Medium confidence: {len(medium_confidence)} possible codes - manual review recommended"
    else:
        return "Low confidence codes detected - may be false positives"

def _calculate_accuracy(detected_codes: List[Dict], expected_codes: List[str]) -> float:
    """Calculate detection accuracy for demo purposes."""
    if not expected_codes:
        return 1.0 if not detected_codes else 0.0
    
    detected_code_strings = [c["code"] for c in detected_codes]
    matches = sum(1 for code in expected_codes if code in detected_code_strings)
    
    return round(matches / len(expected_codes), 2)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🎯 Starting Coupon Finder MCP Server on {host}:{port}")
    print("📧 Ready to detect and organize promotional codes from emails!")
    print("🔗 Connect via: http://localhost:8000/mcp")
    
    mcp.run(
        transport="http",
        host=host,
        port=port
    )
