"""
Invoice & Receipt OCR for SabiSpend
====================================

Extracts text and amounts from:
- Supplier invoices
- Handwritten sales records
- Product price lists
- Receipt images

Uses configurable Vision API endpoint (set in .env)
"""

import os
import logging
import httpx
import base64
import re
from typing import Dict, List, Optional
from config import VISION_API_URL, VISION_API_KEY

logger = logging.getLogger(__name__)


async def recognize_invoice(image_bytes: bytes) -> Dict:
    """
    Extract text and amounts from invoice/receipt image
    
    Args:
        image_bytes: Image data as bytes
    
    Returns:
        Dict with extracted text, amounts, and confidence scores
    """
    if not VISION_API_URL:
        logger.warning("⚠️ VISION_API_URL not configured")
        return {
            "success": False,
            "error": "Vision API not configured",
            "text": "",
            "amounts": []
        }
    
    try:
        logger.info(f"📸 Sending invoice image to Vision API: {VISION_API_URL}")
        
        # Prepare image for API
        b64_image = base64.b64encode(image_bytes).decode()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "image": b64_image,
                "task": "invoice_ocr",
                "extract_amounts": True
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            if VISION_API_KEY:
                headers["Authorization"] = f"Bearer {VISION_API_KEY}"
            
            response = await client.post(
                VISION_API_URL,
                json=payload,
                headers=headers
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"✅ Invoice OCR result: {result}")
            
            # Parse response (format depends on your Vision API)
            # Adjust this based on actual API response structure
            extracted_text = result.get("text", "")
            amounts = result.get("amounts", [])
            
            # Fallback: extract amounts from text if API doesn't provide them
            if not amounts and extracted_text:
                amounts = extract_amounts_from_text(extracted_text)
            
            return {
                "success": True,
                "text": extracted_text,
                "amounts": amounts,
                "confidence": result.get("confidence", 0.0)
            }
            
    except httpx.TimeoutException as e:
        logger.error(f"❌ Invoice OCR timeout: {e}")
        return {
            "success": False,
            "error": "Vision API timeout",
            "text": "",
            "amounts": []
        }
    except httpx.HTTPError as e:
        logger.error(f"❌ Invoice OCR HTTP error: {e}")
        return {
            "success": False,
            "error": f"Vision API error: {e}",
            "text": "",
            "amounts": []
        }
    except Exception as e:
        logger.error(f"❌ Invoice OCR error: {e}")
        return {
            "success": False,
            "error": str(e),
            "text": "",
            "amounts": []
        }


def extract_amounts_from_text(text: str) -> List[Dict]:
    """
    Extract monetary amounts from OCR text
    
    Supports formats:
    - ₦1,234.56
    - N1234.56
    - 1,234.56 naira
    - 1234
    
    Returns:
        List of dicts with {amount: float, text: str, confidence: float}
    """
    amounts = []
    
    # Patterns to match Nigerian currency
    patterns = [
        r'₦\s*([0-9,]+\.?[0-9]*)',  # ₦1,234.56
        r'N\s*([0-9,]+\.?[0-9]*)',   # N1,234.56
        r'([0-9,]+\.?[0-9]*)\s*(?:naira|ngn)',  # 1,234.56 naira
        r'(?:total|amount|price|cost)[\s:]*₦?\s*([0-9,]+\.?[0-9]*)',  # Total: ₦1,234
        r'([0-9,]{4,}\.?[0-9]*)',  # Large numbers (4+ digits)
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            amount_str = match.group(1).replace(',', '')
            try:
                amount_value = float(amount_str)
                if amount_value > 0:
                    amounts.append({
                        "amount": amount_value,
                        "text": match.group(0),
                        "confidence": 0.8
                    })
            except ValueError:
                continue
    
    # Sort by amount (largest first) and remove duplicates
    amounts = sorted(amounts, key=lambda x: x["amount"], reverse=True)
    unique_amounts = []
    seen_values = set()
    
    for amt in amounts:
        if amt["amount"] not in seen_values:
            unique_amounts.append(amt)
            seen_values.add(amt["amount"])
    
    logger.info(f"📊 Extracted {len(unique_amounts)} amounts from text")
    return unique_amounts


async def recognize_sales_record(image_bytes: bytes) -> Dict:
    """
    Extract sales information from handwritten or printed sales record
    
    Args:
        image_bytes: Image data as bytes
    
    Returns:
        Dict with extracted sales data
    """
    # Use same OCR function but with different task hint
    result = await recognize_invoice(image_bytes)
    
    if result["success"]:
        # For sales records, we typically want the total/final amount
        amounts = result.get("amounts", [])
        if amounts:
            # Assume largest amount is the total sales
            total_sales = max(amt["amount"] for amt in amounts)
            result["suggested_total"] = total_sales
            logger.info(f"💰 Suggested total sales: ₦{total_sales:,.2f}")
    
    return result


def convert_to_data_uri(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """
    Convert image bytes to data URI for passing to AI agent
    
    Args:
        image_bytes: Image data
        mime_type: MIME type (image/jpeg, image/png, etc.)
    
    Returns:
        Data URI string
    """
    b64_data = base64.b64encode(image_bytes).decode()
    return f"data:{mime_type};base64,{b64_data}"


def format_amount_list(amounts: List[Dict]) -> str:
    """
    Format extracted amounts for display to user
    
    Args:
        amounts: List of amount dicts from OCR
    
    Returns:
        Formatted string
    """
    if not amounts:
        return "No amounts detected in the image."
    
    lines = []
    for i, amt in enumerate(amounts[:5], 1):  # Show top 5
        lines.append(f"{i}. ₦{amt['amount']:,.2f} ({amt['text']})")
    
    return "\n".join(lines)
