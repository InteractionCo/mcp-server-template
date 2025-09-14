#!/usr/bin/env python3
"""
Coupon Detector Module - Core logic for detecting promo codes and coupons in email content.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CouponCode:
    """Represents a detected coupon code with metadata."""
    code: str
    confidence: float
    context: str
    email_subject: str
    source: str
    detected_at: datetime
    keywords_found: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "code": self.code,
            "confidence": self.confidence,
            "context": self.context,
            "email_subject": self.email_subject,
            "source": self.source,
            "detected_at": self.detected_at.isoformat(),
            "keywords_found": self.keywords_found
        }

class CouponDetector:
    """Advanced coupon code detector with multiple regex patterns and keyword matching."""
    
    def __init__(self):
        # Coupon-related keywords that indicate promotional content
        self.keywords = [
            "coupon", "promo code", "promo", "discount", "% off", "percent off",
            "deal", "offer", "sale", "save", "code", "voucher", "rebate",
            "special offer", "limited time", "exclusive", "flash sale",
            "clearance", "markdown", "reduced", "bargain", "bonus",
            "free shipping", "buy one get one", "bogo", "half price",
            "price drop", "slashed", "cut price", "promotional code",
            "discount code", "savings code", "checkout code", "redeem",
            "apply code", "enter code", "use code"
        ]
        
        # Multiple regex patterns for different coupon code formats
        self.coupon_patterns = [
            # Standard alphanumeric codes (5-15 chars, mixed case)
            r'\b[A-Z0-9]{5,15}\b(?=[\s\.,!]|$)',
            
            # Codes with specific prefixes
            r'\b(?:SAVE|GET|PROMO|DEAL|OFFER|CODE|DISCOUNT|SALE)\d{2,8}\b',
            r'\b(?:SAVE|GET|PROMO|DEAL|OFFER|CODE|DISCOUNT|SALE)[A-Z0-9]{2,8}\b',
            
            # Percentage-based codes
            r'\b[A-Z0-9]*(?:10|15|20|25|30|40|50|60|70|75|80|90)(?:OFF|PERCENT|PCT)[A-Z0-9]*\b',
            
            # Holiday/seasonal codes
            r'\b(?:SUMMER|WINTER|SPRING|FALL|HOLIDAY|XMAS|BLACK|CYBER|FRIDAY|MONDAY)[A-Z0-9]{2,8}\b',
            r'\b[A-Z0-9]{2,8}(?:SUMMER|WINTER|SPRING|FALL|HOLIDAY|XMAS|BLACK|CYBER|FRIDAY|MONDAY)\b',
            
            # Free shipping codes
            r'\b(?:FREE|SHIP|SHIPPING)[A-Z0-9]{2,8}\b',
            r'\b[A-Z0-9]{2,8}(?:FREE|SHIP|SHIPPING)\b',
            
            # Welcome/new customer codes
            r'\b(?:WELCOME|NEW|FIRST|HELLO)[A-Z0-9]{2,8}\b',
            r'\b[A-Z0-9]{2,8}(?:WELCOME|NEW|FIRST|HELLO)\b',
            
            # Brand-specific patterns (common e-commerce patterns)
            r'\b[A-Z]{2,4}\d{4,8}\b',  # Brand initials + numbers
            r'\b\d{4,8}[A-Z]{2,4}\b',  # Numbers + brand initials
            
            # Codes with special characters (but clean alphanumeric extraction)
            r'(?:code[:\s]*)?([A-Z0-9]{4,12})(?=[\s\.,!]|$)',
            
            # Quoted or bracketed codes
            r'["\'\[({]([A-Z0-9]{4,12})["\'\])}]',
            
            # Codes in ALL CAPS sentences
            r'\b[A-Z]{4,12}\b(?=.*(?:checkout|cart|order|purchase|buy))',
        ]
        
        # Compile patterns for better performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.coupon_patterns]
        
        # Common false positives to filter out
        self.false_positives = {
            "UNSUBSCRIBE", "SUBSCRIBE", "EMAIL", "GMAIL", "YAHOO", "HOTMAIL",
            "AMAZON", "GOOGLE", "FACEBOOK", "TWITTER", "INSTAGRAM", "LINKEDIN",
            "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY",
            "JANUARY", "FEBRUARY", "MARCH", "APRIL", "JUNE", "JULY", "AUGUST",
            "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER", "HTTPS", "HTTP",
            "CLICK", "HERE", "LINK", "BUTTON", "IMAGE", "VIDEO", "PHONE",
            "ADDRESS", "CONTACT", "SUPPORT", "HELP", "FAQ", "TERMS", "PRIVACY"
        }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for processing."""
        if not text:
            return ""
        
        # Convert to uppercase for consistent matching
        text = text.upper()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common HTML entities
        text = text.replace('&AMP;', '&').replace('&LT;', '<').replace('&GT;', '>')
        text = text.replace('&NBSP;', ' ').replace('&QUOT;', '"')
        
        return text.strip()
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract coupon-related keywords from text."""
        found_keywords = []
        clean_text = self.clean_text(text)
        
        for keyword in self.keywords:
            if keyword.upper() in clean_text:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def extract_coupon_codes(self, text: str) -> List[Tuple[str, float, str]]:
        """
        Extract potential coupon codes from text.
        Returns list of (code, confidence, context) tuples.
        """
        codes = []
        clean_text = self.clean_text(text)
        
        for pattern in self.compiled_patterns:
            matches = pattern.finditer(clean_text)
            
            for match in matches:
                # Get the actual code (handle group captures)
                if match.groups():
                    code = match.group(1)
                else:
                    code = match.group(0)
                
                # Skip if it's a false positive
                if code in self.false_positives:
                    continue
                
                # Skip if too short or too long
                if len(code) < 4 or len(code) > 15:
                    continue
                
                # Skip if all numbers or all letters
                if code.isdigit() or code.isalpha():
                    if len(code) < 6:  # Allow longer single-type codes
                        continue
                
                # Calculate confidence based on various factors
                confidence = self.calculate_confidence(code, text, clean_text)
                
                # Get context (surrounding text)
                start = max(0, match.start() - 20)
                end = min(len(clean_text), match.end() + 20)
                context = clean_text[start:end].strip()
                
                codes.append((code, confidence, context))
        
        # Remove duplicates and sort by confidence
        unique_codes = {}
        for code, conf, ctx in codes:
            if code not in unique_codes or unique_codes[code][0] < conf:
                unique_codes[code] = (conf, ctx)
        
        return [(code, conf, ctx) for code, (conf, ctx) in unique_codes.items()]
    
    def calculate_confidence(self, code: str, original_text: str, clean_text: str) -> float:
        """Calculate confidence score for a detected code."""
        confidence = 0.5  # Base confidence
        
        # Check for surrounding promotional keywords
        keywords_found = self.extract_keywords(original_text)
        confidence += min(len(keywords_found) * 0.1, 0.3)
        
        # Code format analysis
        if re.match(r'^[A-Z0-9]+$', code):  # All caps alphanumeric
            confidence += 0.1
        
        if any(word in code for word in ['SAVE', 'GET', 'OFF', 'FREE', 'PROMO']):
            confidence += 0.15
        
        if re.search(r'\d{2}(?:OFF|PERCENT)', code):  # Contains percentage
            confidence += 0.2
        
        # Context analysis
        context_keywords = ['use code', 'enter code', 'promo code', 'discount code', 'checkout']
        for keyword in context_keywords:
            if keyword.upper() in clean_text:
                confidence += 0.1
        
        # Length scoring (optimal length is 6-10 characters)
        if 6 <= len(code) <= 10:
            confidence += 0.1
        elif 4 <= len(code) <= 12:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def detect_coupons_in_email(self, subject: str, body: str, sender: str = "") -> List[CouponCode]:
        """
        Main method to detect coupons in an email.
        Returns list of CouponCode objects.
        """
        all_text = f"{subject} {body}"
        
        # First check if email contains coupon keywords
        keywords_found = self.extract_keywords(all_text)
        if not keywords_found:
            logger.info("No coupon keywords found in email")
            return []
        
        logger.info(f"Found keywords: {keywords_found}")
        
        # Extract codes from both subject and body
        subject_codes = self.extract_coupon_codes(subject)
        body_codes = self.extract_coupon_codes(body)
        
        # Combine and create CouponCode objects
        coupon_codes = []
        
        for code, confidence, context in subject_codes + body_codes:
            coupon = CouponCode(
                code=code,
                confidence=confidence,
                context=context,
                email_subject=subject,
                source=sender or "Unknown",
                detected_at=datetime.now(),
                keywords_found=keywords_found
            )
            coupon_codes.append(coupon)
        
        # Sort by confidence (highest first)
        coupon_codes.sort(key=lambda x: x.confidence, reverse=True)
        
        logger.info(f"Detected {len(coupon_codes)} potential coupon codes")
        return coupon_codes
    
    def is_promotional_email(self, subject: str, body: str) -> bool:
        """Check if an email appears to be promotional/contains coupons."""
        keywords_found = self.extract_keywords(f"{subject} {body}")
        return len(keywords_found) > 0
    
    def get_detection_stats(self, coupon_codes: List[CouponCode]) -> Dict:
        """Get statistics about detected coupons."""
        if not coupon_codes:
            return {"total_codes": 0, "avg_confidence": 0, "keywords_found": []}
        
        total_codes = len(coupon_codes)
        avg_confidence = sum(c.confidence for c in coupon_codes) / total_codes
        all_keywords = []
        for c in coupon_codes:
            all_keywords.extend(c.keywords_found)
        unique_keywords = list(set(all_keywords))
        
        return {
            "total_codes": total_codes,
            "avg_confidence": round(avg_confidence, 2),
            "keywords_found": unique_keywords,
            "codes_by_confidence": [
                {"code": c.code, "confidence": c.confidence} 
                for c in coupon_codes
            ]
        }