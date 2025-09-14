#!/usr/bin/env python3
"""
Google Sheets Integration Module - For logging detected coupons to Google Sheets.
"""

import os
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from google.auth.exceptions import RefreshError

from coupon_detector import CouponCode

logger = logging.getLogger(__name__)

class SheetsLogger:
    """Manages logging coupon codes to Google Sheets."""
    
    def __init__(self, credentials_json: Optional[str] = None, sheet_name: str = "Coupon Tracker"):
        """
        Initialize the sheets logger.
        
        Args:
            credentials_json: JSON string of service account credentials
            sheet_name: Name of the Google Sheet to create/use
        """
        self.sheet_name = sheet_name
        self.gc = None
        self.sheet = None
        self.worksheet = None
        
        if credentials_json:
            self.setup_credentials(credentials_json)
    
    def setup_credentials(self, credentials_json: str) -> bool:
        """Setup Google Sheets API credentials."""
        try:
            # Parse credentials JSON
            creds_dict = json.loads(credentials_json)
            
            # Setup credentials with required scopes
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            
            # Initialize gspread client
            self.gc = gspread.authorize(credentials)
            
            logger.info("Google Sheets credentials setup successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Google Sheets credentials: {e}")
            return False
    
    def create_or_get_sheet(self) -> bool:
        """Create a new Google Sheet or get existing one."""
        if not self.gc:
            logger.error("Google Sheets client not initialized")
            return False
        
        try:
            # Try to open existing sheet
            try:
                self.sheet = self.gc.open(self.sheet_name)
                logger.info(f"Opened existing sheet: {self.sheet_name}")
            except gspread.SpreadsheetNotFound:
                # Create new sheet
                self.sheet = self.gc.create(self.sheet_name)
                logger.info(f"Created new sheet: {self.sheet_name}")
            
            # Get or create the main worksheet
            try:
                self.worksheet = self.sheet.worksheet("Coupons")
            except gspread.WorksheetNotFound:
                self.worksheet = self.sheet.add_worksheet(title="Coupons", rows=1000, cols=10)
                # Set up headers
                headers = [
                    "Date Detected", "Coupon Code", "Confidence", "Email Subject", 
                    "Sender", "Context", "Keywords Found", "Status", "Used Date", "Notes"
                ]
                self.worksheet.append_row(headers)
                
                # Format header row
                self.worksheet.format("A1:J1", {
                    "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 1.0},
                    "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create/get Google Sheet: {e}")
            return False
    
    def log_coupon(self, coupon: CouponCode, status: str = "New") -> bool:
        """Log a single coupon to the sheet."""
        if not self.worksheet:
            logger.error("Worksheet not initialized")
            return False
        
        try:
            # Prepare row data
            row_data = [
                coupon.detected_at.strftime("%Y-%m-%d %H:%M:%S"),
                coupon.code,
                str(coupon.confidence),
                coupon.email_subject,
                coupon.source,
                coupon.context,
                ", ".join(coupon.keywords_found),
                status,
                "",  # Used Date (empty initially)
                ""   # Notes (empty initially)
            ]
            
            # Add row to sheet
            self.worksheet.append_row(row_data)
            
            logger.info(f"Successfully logged coupon: {coupon.code}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log coupon to sheet: {e}")
            return False
    
    def log_multiple_coupons(self, coupons: List[CouponCode]) -> Dict[str, int]:
        """Log multiple coupons at once."""
        results = {"success": 0, "failed": 0}
        
        for coupon in coupons:
            if self.log_coupon(coupon):
                results["success"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    def get_existing_coupons(self) -> List[str]:
        """Get list of existing coupon codes to avoid duplicates."""
        if not self.worksheet:
            return []
        
        try:
            # Get all values from column B (Coupon Code)
            values = self.worksheet.col_values(2)  # Column B is index 2
            # Skip header row
            return values[1:] if len(values) > 1 else []
            
        except Exception as e:
            logger.error(f"Failed to get existing coupons: {e}")
            return []
    
    def update_coupon_status(self, coupon_code: str, status: str, used_date: str = "", notes: str = "") -> bool:
        """Update the status of a coupon (e.g., mark as used)."""
        if not self.worksheet:
            return False
        
        try:
            # Find the row with this coupon code
            cell = self.worksheet.find(coupon_code)
            if cell:
                row = cell.row
                
                # Update status (column H)
                self.worksheet.update_cell(row, 8, status)
                
                # Update used date if provided (column I)
                if used_date:
                    self.worksheet.update_cell(row, 9, used_date)
                
                # Update notes if provided (column J)
                if notes:
                    self.worksheet.update_cell(row, 10, notes)
                
                logger.info(f"Updated coupon {coupon_code} status to {status}")
                return True
            else:
                logger.warning(f"Coupon code {coupon_code} not found in sheet")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update coupon status: {e}")
            return False
    
    def get_sheet_url(self) -> Optional[str]:
        """Get the URL of the Google Sheet."""
        if self.sheet:
            return self.sheet.url
        return None
    
    def get_coupon_statistics(self) -> Dict:
        """Get statistics about logged coupons."""
        if not self.worksheet:
            return {}
        
        try:
            # Get all data
            all_values = self.worksheet.get_all_values()
            
            if len(all_values) <= 1:  # Only header or empty
                return {"total_coupons": 0, "status_breakdown": {}}
            
            # Skip header row
            data = all_values[1:]
            
            total_coupons = len(data)
            status_breakdown = {}
            confidence_sum = 0
            confidence_count = 0
            
            for row in data:
                if len(row) >= 8:  # Ensure we have status column
                    status = row[7] if row[7] else "Unknown"
                    status_breakdown[status] = status_breakdown.get(status, 0) + 1
                    
                    # Calculate average confidence
                    try:
                        confidence = float(row[2])
                        confidence_sum += confidence
                        confidence_count += 1
                    except (ValueError, IndexError):
                        pass
            
            avg_confidence = confidence_sum / confidence_count if confidence_count > 0 else 0
            
            return {
                "total_coupons": total_coupons,
                "status_breakdown": status_breakdown,
                "average_confidence": round(avg_confidence, 2),
                "sheet_url": self.get_sheet_url()
            }
            
        except Exception as e:
            logger.error(f"Failed to get coupon statistics: {e}")
            return {}

def create_sample_credentials() -> str:
    """Create a sample credentials JSON structure for documentation."""
    sample_creds = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "your-private-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
        "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
    }
    return json.dumps(sample_creds, indent=2)