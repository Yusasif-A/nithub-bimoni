"""
Scam & Message Verification for SabiSpend
==========================================

Analyzes forwarded SMS and WhatsApp messages to detect:
- Fake bank alerts
- Fraudulent transfer requests
- Phishing attempts
- Suspicious payment messages
- Impersonation scams

Helps low-literacy users identify scams before losing money.
"""

import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


# Common Nigerian bank alert patterns
BANK_ALERT_PATTERNS = [
    r'(?:credit|debit|transfer)',
    r'(?:acct|account|a\/c)',
    r'(?:amt|amount|sum)',
    r'(?:bal|balance|avail)',
    r'(?:ref|reference)',
]

# Red flags for scam messages
SCAM_INDICATORS = {
    "urgent_action": [
        r'urgent(?:ly)?',
        r'immediate(?:ly)?',
        r'act (?:now|fast|quickly)',
        r'within \d+ (?:hours?|minutes?)',
        r'limited time',
        r'expires? (?:soon|today)',
    ],
    "suspicious_requests": [
        r'(?:send|share|provide).{0,20}(?:pin|password|otp|code)',
        r'verify.{0,20}(?:account|details|information)',
        r'update.{0,20}(?:account|details|kyc)',
        r'confirm.{0,20}(?:identity|details)',
        r'click.{0,20}(?:link|here|below)',
    ],
    "financial_pressure": [
        r'(?:win|won).{0,20}(?:\d+|money|prize|naira)',
        r'claim.{0,20}(?:prize|reward|bonus)',
        r'pay.{0,20}(?:fee|charge|tax)',
        r'account.{0,20}(?:blocked|suspended|frozen)',
        r'will be.{0,20}(?:closed|deleted|removed)',
    ],
    "impersonation": [
        r'(?:i am|this is).{0,30}(?:bank|manager|cbn|efcc)',
        r'bank.{0,20}(?:officer|staff|official)',
        r'customer.{0,20}(?:service|care|support)',
        r'help.?desk',
    ],
    "fake_bank_alerts": [
        r'credited.{0,20}account',
        r'debited.{0,20}account',
        r'bal:?.{0,5}(?:ngn|₦)?\s*\d',
    ],
    "suspicious_links": [
        r'(?:bit\.ly|tinyurl|goo\.gl)',
        r'(?:click|tap).{0,20}(?:link|here)',
        r'http[s]?://(?!.*(?:gtbank|zenith|firstbank|access|uba|union))',
    ],
}

# Legitimate bank sender patterns
LEGITIMATE_BANKS = [
    r'gtbank', r'gtb', r'guaranty trust',
    r'zenith', r'zenit',
    r'first bank', r'firstbank',
    r'access bank', r'accessbank',
    r'uba', r'united bank',
    r'union bank', r'unionbank',
    r'fidelity', r'fcmb',
    r'stanbic', r'sterling',
    r'ecobank', r'polaris',
    r'wema', r'keystone',
]


def analyze_message(message_text: str, sender: str = "") -> Dict:
    """
    Analyze a forwarded message for scam indicators
    
    Args:
        message_text: The message content to analyze
        sender: Sender identifier (phone number, name, etc.)
    
    Returns:
        Dict with risk_level, risk_score, indicators, and explanation
    """
    message_lower = message_text.lower()
    sender_lower = sender.lower()
    
    # Count red flags
    indicators_found = {
        "urgent_action": [],
        "suspicious_requests": [],
        "financial_pressure": [],
        "impersonation": [],
        "fake_bank_alerts": [],
        "suspicious_links": [],
    }
    
    risk_score = 0
    
    # Check each category
    for category, patterns in SCAM_INDICATORS.items():
        for pattern in patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                indicators_found[category].append(pattern.replace(r'\d+', 'number'))
                risk_score += 1
    
    # Check if sender claims to be a bank
    claims_to_be_bank = any(re.search(bank, sender_lower) for bank in LEGITIMATE_BANKS)
    is_likely_legit_bank = claims_to_be_bank and risk_score <= 1
    
    # Check for bank alert structure
    has_bank_alert_structure = sum(
        1 for pattern in BANK_ALERT_PATTERNS 
        if re.search(pattern, message_lower)
    ) >= 3
    
    # Determine risk level
    if risk_score == 0 and has_bank_alert_structure:
        risk_level = "low"
        risk_color = "🟢"
        explanation = "This looks like a normal bank alert."
    elif risk_score <= 1 and is_likely_legit_bank:
        risk_level = "low"
        risk_color = "🟢"
        explanation = "This appears to be from a legitimate bank."
    elif risk_score <= 2:
        risk_level = "medium"
        risk_color = "🟡"
        explanation = "Be careful. This message has some warning signs."
    elif risk_score <= 4:
        risk_level = "high"
        risk_color = "🟠"
        explanation = "This message has several warning signs. Be very careful."
    else:
        risk_level = "very_high"
        risk_color = "🔴"
        explanation = "This is very likely a scam. Do not respond or send money."
    
    # Remove empty categories
    indicators_found = {k: v for k, v in indicators_found.items() if v}
    
    logger.info(f"🔍 Scam analysis: {risk_level} risk ({risk_score} indicators)")
    
    return {
        "risk_level": risk_level,
        "risk_color": risk_color,
        "risk_score": risk_score,
        "indicators": indicators_found,
        "explanation": explanation,
        "is_bank_alert": has_bank_alert_structure,
        "claims_to_be_bank": claims_to_be_bank,
    }


def format_analysis_for_user(analysis: Dict, message_preview: str = "") -> str:
    """
    Format scam analysis results in simple language for low-literacy users
    
    Args:
        analysis: Result from analyze_message()
        message_preview: First 100 chars of the message
    
    Returns:
        Formatted message for WhatsApp
    """
    risk_level = analysis["risk_level"]
    risk_color = analysis["risk_color"]
    explanation = analysis["explanation"]
    indicators = analysis["indicators"]
    
    # Build response
    lines = [
        f"{risk_color} *Message Safety Check*",
        "",
        f"*Result:* {explanation}",
        "",
    ]
    
    if risk_level in ["high", "very_high"]:
        lines.append("⚠️ *Warning Signs Detected:*")
        
        warning_messages = {
            "urgent_action": "• Pressuring you to act quickly",
            "suspicious_requests": "• Asking for passwords or PIN",
            "financial_pressure": "• Threatening account closure or offering prizes",
            "impersonation": "• Pretending to be bank staff",
            "fake_bank_alerts": "• May be a fake bank alert",
            "suspicious_links": "• Contains suspicious links",
        }
        
        for category in indicators:
            if category in warning_messages:
                lines.append(warning_messages[category])
        
        lines.append("")
        lines.append("🛑 *What to do:*")
        lines.append("• Do NOT send money")
        lines.append("• Do NOT share your PIN or password")
        lines.append("• Do NOT click any links")
        lines.append("• Call your bank directly to confirm")
        
    elif risk_level == "medium":
        lines.append("⚠️ *Be Careful:*")
        lines.append("• Double-check the sender")
        lines.append("• Call your bank if unsure")
        lines.append("• Never share your PIN or password")
        
    elif risk_level == "low":
        if analysis["is_bank_alert"]:
            lines.append("✅ This looks like a real bank alert.")
        else:
            lines.append("✅ This message appears safe, but always stay alert.")
    
    return "\n".join(lines)


def get_scam_prevention_tips() -> List[str]:
    """
    Get list of scam prevention tips for users
    
    Returns:
        List of simple scam prevention tips
    """
    return [
        "Your bank will NEVER ask for your PIN or password.",
        "Be suspicious of messages with urgent requests for money.",
        "Always call your bank directly to confirm unusual alerts.",
        "Real bank alerts come from official bank numbers you know.",
        "Do not click links in unexpected messages about your account.",
        "If a prize or offer sounds too good to be true, it probably is.",
        "Never send money to 'verify' your account or 'claim' a prize.",
        "Check the sender carefully - scammers use similar names to real banks.",
    ]
