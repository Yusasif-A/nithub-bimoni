"""
Expense & Sales Tracker for SabiSpend
======================================

Tracks daily business expenses (stock purchases) and sales for informal traders.
Calculates profit, suggests savings amounts, and provides financial insights.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _get_collection():
    """Get MongoDB collection for expense tracking"""
    uri = os.getenv("MONGO_URI")
    if not uri:
        logger.error("MONGO_URI not set")
        return None
    
    try:
        client = MongoClient(uri, server_api=ServerApi("1"))
        db = client.get_database("SabiSpend")
        col = db.get_collection("daily_transactions")
        
        # Create indexes for efficient queries
        col.create_index([("phone_number", ASCENDING), ("date", DESCENDING)])
        col.create_index([("phone_number", ASCENDING), ("transaction_type", ASCENDING)])
        
        return col
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        return None


def save_expense(phone_number: str, amount: float, description: str, category: str = "stock") -> Dict:
    """
    Record a business expense (e.g., stock purchase, supplier payment)
    
    Args:
        phone_number: User's phone number
        amount: Expense amount in Naira
        description: What was purchased (e.g., "tomatoes from supplier")
        category: Expense type (stock, transport, rent, etc.)
    
    Returns:
        Dict with success status and expense_id
    """
    col = _get_collection()
    if col is None:
        return {"error": "Database unavailable", "success": False}
    
    try:
        entry = {
            "phone_number": phone_number,
            "transaction_type": "expense",
            "amount": amount,
            "description": description,
            "category": category,
            "date": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0),
            "timestamp": datetime.now(timezone.utc)
        }
        
        result = col.insert_one(entry)
        logger.info(f"✅ Expense saved: {phone_number} - ₦{amount:,.2f} ({description})")
        
        return {
            "success": True,
            "expense_id": str(result.inserted_id),
            "amount": amount,
            "description": description
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to save expense: {e}")
        return {"error": str(e), "success": False}


def save_sales(phone_number: str, amount: float, description: str = "Daily sales") -> Dict:
    """
    Record daily sales/revenue
    
    Args:
        phone_number: User's phone number
        amount: Sales amount in Naira
        description: Sales description
    
    Returns:
        Dict with success status and sales_id
    """
    col = _get_collection()
    if col is None:
        return {"error": "Database unavailable", "success": False}
    
    try:
        entry = {
            "phone_number": phone_number,
            "transaction_type": "sales",
            "amount": amount,
            "description": description,
            "date": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0),
            "timestamp": datetime.now(timezone.utc)
        }
        
        result = col.insert_one(entry)
        logger.info(f"✅ Sales saved: {phone_number} - ₦{amount:,.2f}")
        
        return {
            "success": True,
            "sales_id": str(result.inserted_id),
            "amount": amount,
            "description": description
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to save sales: {e}")
        return {"error": str(e), "success": False}


def calculate_daily_profit(phone_number: str, date: Optional[datetime] = None) -> Dict:
    """
    Calculate profit for a specific day
    
    Args:
        phone_number: User's phone number
        date: Date to calculate (defaults to today)
    
    Returns:
        Dict with expenses, sales, profit, and savings suggestion
    """
    col = _get_collection()
    if col is None:
        return {"error": "Database unavailable"}
    
    try:
        # Default to today
        if date is None:
            date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get all transactions for this day
        transactions = list(col.find({
            "phone_number": phone_number,
            "date": date
        }))
        
        # Calculate totals
        total_expenses = sum(t["amount"] for t in transactions if t["transaction_type"] == "expense")
        total_sales = sum(t["amount"] for t in transactions if t["transaction_type"] == "sales")
        profit = total_sales - total_expenses
        
        # Suggest savings amount (10-20% of profit if positive)
        suggested_savings = 0
        if profit > 0:
            suggested_savings = round(profit * 0.15, 2)  # 15% of profit
        
        result = {
            "date": date.strftime("%Y-%m-%d"),
            "total_expenses": total_expenses,
            "total_sales": total_sales,
            "profit": profit,
            "suggested_savings": suggested_savings,
            "expense_count": sum(1 for t in transactions if t["transaction_type"] == "expense"),
            "sales_count": sum(1 for t in transactions if t["transaction_type"] == "sales")
        }
        
        logger.info(f"📊 Daily profit for {phone_number}: ₦{profit:,.2f} (Sales: ₦{total_sales:,.2f}, Expenses: ₦{total_expenses:,.2f})")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to calculate profit: {e}")
        return {"error": str(e)}


def get_weekly_summary(phone_number: str) -> Dict:
    """
    Get 7-day financial summary
    
    Returns:
        Dict with weekly totals and trends
    """
    col = _get_collection()
    if col is None:
        return {"error": "Database unavailable"}
    
    try:
        # Get last 7 days
        end_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=7)
        
        transactions = list(col.find({
            "phone_number": phone_number,
            "date": {"$gte": start_date, "$lte": end_date}
        }))
        
        total_expenses = sum(t["amount"] for t in transactions if t["transaction_type"] == "expense")
        total_sales = sum(t["amount"] for t in transactions if t["transaction_type"] == "sales")
        weekly_profit = total_sales - total_expenses
        
        return {
            "period": "7 days",
            "total_expenses": total_expenses,
            "total_sales": total_sales,
            "profit": weekly_profit,
            "average_daily_profit": round(weekly_profit / 7, 2) if weekly_profit > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get weekly summary: {e}")
        return {"error": str(e)}


def get_transaction_history(phone_number: str, days: int = 7) -> List[Dict]:
    """
    Get recent transaction history
    
    Args:
        phone_number: User's phone number
        days: Number of days to retrieve
    
    Returns:
        List of transactions
    """
    col = _get_collection()
    if col is None:
        return []
    
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        transactions = list(col.find(
            {
                "phone_number": phone_number,
                "timestamp": {"$gte": cutoff_date}
            },
            {"_id": 0, "phone_number": 0}
        ).sort("timestamp", DESCENDING).limit(20))
        
        return transactions
        
    except Exception as e:
        logger.error(f"❌ Failed to get transaction history: {e}")
        return []


def get_all_user_threads() -> List[str]:
    """
    Get all unique phone numbers for daily tips/reminders
    
    Returns:
        List of phone numbers
    """
    uri = os.getenv("MONGO_URI")
    if not uri:
        return []
    
    try:
        client = MongoClient(uri, server_api=ServerApi("1"))
        db = client.get_database("SabiSpend")
        col = db.get_collection("daily_transactions")
        
        phone_numbers = col.distinct("phone_number")
        logger.info(f"📋 Found {len(phone_numbers)} active users")
        return [n for n in phone_numbers if n]
        
    except Exception as e:
        logger.error(f"❌ get_all_user_threads error: {e}")
        return []
