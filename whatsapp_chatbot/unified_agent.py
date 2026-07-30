"""
SabiSpend Unified Agent
========================

AI Money Assistant for low-literacy Nigerian traders.
Handles expense tracking, profit calculation, savings, and scam detection.
"""

import os
import re
import logging
import asyncio
from typing import Optional, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from memory import get_memory
from expense_tracker import save_expense, save_sales, calculate_daily_profit, get_weekly_summary
from bmoni_client import (
    bmoni_client, get_or_create_bmoni_user, get_user_balance_naira,
    get_deposit_account_details, ensure_wallet_created,
    request_send_money as bmoni_request_send_money,
    confirm_send_money as bmoni_confirm_send_money,
)
from scam_detector import analyze_message, format_analysis_for_user
from invoice_ocr import recognize_invoice, recognize_sales_record, extract_amounts_from_text
from bmoni_store import bmoni_store
from sabispend_prompt import (
    SABISPEND_SYSTEM_PROMPT,
    SABISPEND_VOICE_SYSTEM_PROMPT
)

from dotenv import load_dotenv
load_dotenv()

memory = get_memory()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache disabled for real-time responses
cache_enabled = False

# Current user phone number (for tool context)
_current_phone_number: str = ""
_current_user_name: str = ""


# ===================== HELPER FUNCTIONS =====================

def _normalize_phone(phone_number: str) -> str:
    """Normalize phone number to include + prefix for consistency"""
    phone = phone_number.strip()
    if not phone.startswith("+"):
        return f"+{phone}"
    return phone


def _get_bmoni_user_id(phone_number: str) -> Optional[str]:
    """Get stored BMONI user ID from database"""
    try:
        phone = _normalize_phone(phone_number)
        doc = bmoni_store.get_by_phone(phone)
        if doc:
            return doc.get("bmoni_user_id")
    except Exception as e:
        logger.error(f"❌ Error getting BMONI user ID: {e}")
    return None


def _store_bmoni_user_id(phone_number: str, bmoni_user_id: str) -> bool:
    """Store BMONI user ID in database"""
    try:
        phone = _normalize_phone(phone_number)
        bmoni_store.save_user(phone, bmoni_user_id)
        logger.info(f"✅ Stored BMONI user ID for {phone}")
        return True
    except Exception as e:
        logger.error(f"❌ Error storing BMONI user ID: {e}")
        return False


async def _ensure_bmoni_user(phone_number: str, user_name: str) -> Optional[str]:
    """
    Get or create BMONI user AND wallet, returns bmoniUserId
    
    This function now ensures:
    1. BMONI user account exists
    2. EVM keypair generated and stored (encrypted)
    3. Wallet created and activated (server-side signing)
    
    All happens automatically, no user action required.
    """
    # Normalize phone number
    phone = _normalize_phone(phone_number)
    
    # Check database first
    existing = bmoni_store.get_by_phone(phone)
    if existing and existing.get("bmoni_user_id"):
        bmoni_user_id = existing["bmoni_user_id"]
        logger.info(f"✅ Found existing BMONI user: {bmoni_user_id}")
        
        # Check if wallet exists, create if not
        if not existing.get("wallet"):
            logger.info(f"📝 User exists but wallet not created yet - creating now...")
            wallet_result = await ensure_wallet_created(phone, bmoni_user_id)
            if not wallet_result.get("success"):
                logger.warning(f"⚠️ Wallet creation failed: {wallet_result.get('error')}")
        
        return bmoni_user_id
    
    # Create new BMONI user
    logger.info(f"📝 Creating new BMONI user for {phone}")
    bmoni_user_id = await get_or_create_bmoni_user(phone, user_name)
    
    if not bmoni_user_id:
        return None
    
    # Create wallet automatically (server-side signing)
    logger.info(f"🔐 Creating wallet for new user {bmoni_user_id}...")
    wallet_result = await ensure_wallet_created(phone, bmoni_user_id)
    
    if wallet_result.get("success"):
        logger.info(f"🎉 User and wallet setup complete!")
    else:
        logger.warning(f"⚠️ Wallet creation failed: {wallet_result.get('error')}")
        logger.warning(f"   User can still use expense tracking, wallet creation will retry later")
    
    return bmoni_user_id


# ===================== TOOLS =====================

@tool
async def log_expense(amount: float, description: str, category: str = "stock") -> str:
    """
    Record a business expense (stock purchase, supplier payment, etc.)
    
    Args:
        amount: Expense amount in Naira (e.g., 12000 for ₦12,000)
        description: What was purchased (e.g., "tomatoes from supplier", "rice", "transport")
        category: Expense type (stock, transport, rent, utilities)
    
    Returns:
        Confirmation message
    
    Call this when user says:
    - "I bought tomatoes for ₦12,000"
    - "I spent 15,000 on rice"
    - "Transport cost me 2,000 naira"
    """
    global _current_phone_number
    if not _current_phone_number:
        return "Could not save expense — user not identified."
    
    try:
        phone = _normalize_phone(_current_phone_number)
        result = save_expense(
            phone_number=phone,
            amount=amount,
            description=description,
            category=category
        )
        
        if "error" in result:
            return f"Could not save expense: {result['error']}"
        
        logger.info(f"✅ Expense logged: ₦{amount:,.2f} - {description}")
        return f"✅ Recorded. You spent ₦{amount:,.2f} on {description} today."
        
    except Exception as e:
        logger.error(f"❌ log_expense error: {e}")
        return "Could not save expense at this time."


@tool
async def log_sales(amount: float, description: str = "Daily sales") -> str:
    """
    Record daily sales/revenue
    
    Args:
        amount: Sales amount in Naira (e.g., 25000 for ₦25,000)
        description: Sales description (optional)
    
    Returns:
        Confirmation message
    
    Call this when user says:
    - "I sold ₦25,000 today"
    - "My sales today is 30,000"
    - "I made 18 thousand naira"
    """
    global _current_phone_number
    if not _current_phone_number:
        return "Could not save sales — user not identified."
    
    try:
        phone = _normalize_phone(_current_phone_number)
        result = save_sales(
            phone_number=phone,
            amount=amount,
            description=description
        )
        
        if "error" in result:
            return f"Could not save sales: {result['error']}"
        
        logger.info(f"✅ Sales logged: ₦{amount:,.2f}")
        return f"✅ Recorded. You sold ₦{amount:,.2f} today."
        
    except Exception as e:
        logger.error(f"❌ log_sales error: {e}")
        return "Could not save sales at this time."


@tool
async def calculate_profit() -> str:
    """
    Calculate today's profit (sales minus expenses)
    
    Returns:
        Profit summary with suggested savings amount
    
    Call this:
    - After logging sales
    - When user asks "how much profit did I make?"
    - At end of day to show results
    """
    global _current_phone_number
    if not _current_phone_number:
        return "Could not calculate profit — user not identified."
    
    try:
        phone = _normalize_phone(_current_phone_number)
        result = calculate_daily_profit(phone)
        
        if "error" in result:
            return f"Could not calculate profit: {result['error']}"
        
        expenses = result.get("total_expenses", 0)
        sales = result.get("total_sales", 0)
        profit = result.get("profit", 0)
        suggested_savings = result.get("suggested_savings", 0)
        
        if profit > 0:
            return (
                f"📊 Today's Summary:\n"
                f"• Sales: ₦{sales:,.2f}\n"
                f"• Expenses: ₦{expenses:,.2f}\n"
                f"• Profit: ₦{profit:,.2f}\n\n"
                f"💡 Suggested savings: ₦{suggested_savings:,.2f}"
            )
        elif profit == 0:
            return (
                f"📊 Today's Summary:\n"
                f"• Sales: ₦{sales:,.2f}\n"
                f"• Expenses: ₦{expenses:,.2f}\n"
                f"• Profit: ₦0 (Break even)"
            )
        else:
            return (
                f"📊 Today's Summary:\n"
                f"• Sales: ₦{sales:,.2f}\n"
                f"• Expenses: ₦{expenses:,.2f}\n"
                f"• Loss: ₦{abs(profit):,.2f}"
            )
        
    except Exception as e:
        logger.error(f"❌ calculate_profit error: {e}")
        return "Could not calculate profit at this time."


@tool
async def check_balance() -> str:
    """
    Check user's BMONI wallet balance
    
    Returns:
        Current wallet balance in Naira
    
    Call this when user asks:
    - "How much money do I have?"
    - "Check my balance"
    - "What's in my wallet?"
    """
    global _current_phone_number, _current_user_name
    if not _current_phone_number:
        return "Could not check balance — user not identified."
    
    try:
        phone = _normalize_phone(_current_phone_number)
        # Get or create BMONI user
        bmoni_user_id = await _ensure_bmoni_user(phone, _current_user_name)
        
        if not bmoni_user_id:
            return "⚠️ Could not access wallet. Please ensure you have completed wallet setup."
        
        # Get balance
        balance = await get_user_balance_naira(bmoni_user_id)
        
        logger.info(f"💰 Balance check: ₦{balance:,.2f}")
        return f"💰 Your BMONI wallet balance: ₦{balance:,.2f}"
        
    except Exception as e:
        logger.error(f"❌ check_balance error: {e}")
        return "Could not check balance at this time. Please try again."


@tool
async def save_to_wallet(amount: float) -> str:
    """
    Transfer money to user's BMONI savings wallet
    
    Args:
        amount: Amount to save in Naira
    
    Returns:
        Confirmation message or instructions
    
    Call this when user agrees to save:
    - "Yes, save 2000"
    - "Move 1500 to savings"
    - "Save it"
    
    Note: BMONI wallet transactions require EVM signing via separate signer page
    """
    global _current_phone_number, _current_user_name
    if not _current_phone_number:
        return "Could not save money — user not identified."
    
    try:
        phone = _normalize_phone(_current_phone_number)
        # Get or create BMONI user
        bmoni_user_id = await _ensure_bmoni_user(phone, _current_user_name)
        
        if not bmoni_user_id:
            return "⚠️ Could not access wallet. Please ensure you have completed wallet setup."
        
        # Check wallet status first
        status_result = await bmoni_client.get_wallet_status(bmoni_user_id)
        
        if not status_result.get("success"):
            return (
                "⚠️ Your BMONI wallet needs to be activated first. "
                "Please complete the wallet setup process to start saving."
            )
        
        # Get deposit account details to show user where to send money
        deposit_info = await get_deposit_account_details(bmoni_user_id)
        
        if deposit_info.get("success") and deposit_info.get("account_number"):
            return (
                f"💰 To save ₦{amount:,.2f} to your BMONI wallet:\n\n"
                f"Transfer to:\n"
                f"• Account: {deposit_info['account_number']}\n"
                f"• Bank: {deposit_info['bank_name']}\n"
                f"• Name: {deposit_info['account_name']}\n\n"
                f"Your money will reflect in your wallet instantly! 🎉"
            )
        else:
            return (
                "⚠️ Could not get your deposit account details. "
                "Please try again or contact support."
            )
        
    except Exception as e:
        logger.error(f"❌ save_to_wallet error: {e}")
        return "Could not process savings request at this time. Please try again."


@tool
async def request_send_money(recipient_phone: str, amount: float) -> str:
    """
    Start sending money to another SabiSpend user. Does NOT move any money yet
    — it sends a one-time confirmation code to the sender's own WhatsApp number.
    The user must reply with that code, at which point confirm_send_money is
    called separately to actually complete the transfer.

    Args:
        recipient_phone: Recipient's phone number (e.g., "08012345678" or "+2348012345678")
        amount: Amount to send in Naira (e.g., 1000 for ₦1,000)

    Returns:
        Confirmation that a code was sent, or an error explaining why the
        transfer can't proceed (insufficient balance, recipient has no wallet,
        recipient has no active NGN wallet, etc.)

    Call this when user says:
    - "Send 1000 naira to 08012345678"
    - "Transfer 5000 to my friend 08098765432"
    - "Pay 2000 to 0801234567"
    Do not call confirm_send_money in the same turn — wait for the user's
    next message with the code.
    """
    global _current_phone_number, _current_user_name
    if not _current_phone_number:
        return "Could not start the transfer — user not identified."

    try:
        phone = _normalize_phone(_current_phone_number)
        recipient_normalized = _normalize_phone(recipient_phone)

        bmoni_user_id = await _ensure_bmoni_user(phone, _current_user_name)
        if not bmoni_user_id:
            return "⚠️ Could not access your wallet. Please ensure you have completed wallet setup."

        sender_account = bmoni_store.get_by_phone(phone)
        if not sender_account or not sender_account.get("wallet"):
            return "⚠️ You don't have a wallet yet. Complete wallet setup first."
        sender_wallet_id = sender_account["wallet"].get("id")

        result = await bmoni_request_send_money(
            sender_phone=phone,
            sender_bmoni_user_id=bmoni_user_id,
            sender_wallet_id=sender_wallet_id,
            recipient_phone=recipient_normalized,
            amount=amount,
        )

        if not result.get("success"):
            return f"⚠️ {result.get('error', 'Could not start the transfer.')}"

        logger.info(f"📤 Confirmation code sent for {phone} → {recipient_normalized} (₦{amount:,.2f})")
        return (
            f"A confirmation code has been sent to your WhatsApp number. "
            f"Reply with that code to confirm sending ₦{amount:,.2f} to {recipient_phone}."
        )

    except Exception as e:
        logger.error(f"❌ request_send_money error: {e}")
        return "Could not start the transfer at this time. Please try again."


@tool
async def confirm_send_money(code: str) -> str:
    """
    Complete a money transfer that was already started with request_send_money,
    using the confirmation code the user was sent and just replied with.

    Args:
        code: The confirmation code the user typed or spoke back (digits only,
              e.g. "483920")

    Returns:
        Success confirmation once the transfer completes, or an error if the
        code is wrong, expired, or there's no pending transfer to confirm.

    Call this when the user's message looks like a short numeric code shortly
    after a request_send_money confirmation was sent — do not call this for any
    other purpose, and never invent or guess a code yourself.
    """
    global _current_phone_number
    if not _current_phone_number:
        return "Could not confirm the transfer — user not identified."

    try:
        phone = _normalize_phone(_current_phone_number)
        result = await bmoni_confirm_send_money(sender_phone=phone, code=code)

        if not result.get("success"):
            return f"⚠️ {result.get('error', 'Could not confirm the transfer.')}"

        logger.info(
            f"✅ Money sent: ₦{result['amount']:,.2f} from {phone} to {result['recipient_phone']}"
        )
        return f"✅ Sent ₦{result['amount']:,.2f} to {result['recipient_phone']} successfully!"

    except Exception as e:
        logger.error(f"❌ confirm_send_money error: {e}")
        return "Could not confirm the transfer at this time. Please try again."


@tool
async def verify_message(message_text: str, sender: str = "") -> str:
    """
    Check if a forwarded SMS or WhatsApp message is a scam
    
    Args:
        message_text: The message content to verify
        sender: Sender name/number (optional)
    
    Returns:
        Scam analysis with risk level and advice
    
    Call this when user forwards a message asking:
    - "Is this real?"
    - "Check this message"
    - [forwards bank alert or suspicious text]
    """
    try:
        analysis = analyze_message(message_text, sender)
        formatted_result = format_analysis_for_user(analysis, message_text[:100])
        
        logger.info(f"🔍 Message verified: {analysis['risk_level']} risk")
        return formatted_result
        
    except Exception as e:
        logger.error(f"❌ verify_message error: {e}")
        return "Could not verify message at this time."


def is_prompt_injection_attempt(user_input: str) -> bool:
    """Detect prompt injection attempts"""
    clean = re.sub(r'\[.*?\]:\s*', '', user_input.lower()).strip()
    keywords = ["prompt", "system message", "instructions", "ignore previous", "forget your", "act as", "you are now", "pretend you"]
    if any(kw in clean for kw in keywords):
        return True
    patterns = [
        r'what\s+were\s+you\s+(told|given|instructed)',
        r'pretend.*?(you\s+are|to\s+be)',
    ]
    return any(re.search(p, clean) for p in patterns)


def contains_system_prompt_leak(text: str) -> bool:
    """Check if response contains system prompt leaks"""
    text_lower = text.lower()
    prompt_leaks = ["system prompt", "my instructions", "i was told to"]
    return any(term in text_lower for term in prompt_leaks)


def _strip_images_from_history(history: list) -> list:
    """Replace image_url content in old messages with placeholder"""
    cleaned = []
    for msg in history:
        if isinstance(msg, HumanMessage) and isinstance(msg.content, list):
            new_parts = []
            for part in msg.content:
                if isinstance(part, dict) and part.get("type") == "image_url":
                    new_parts.append({"type": "text", "text": "[image sent earlier]"})
                else:
                    new_parts.append(part)
            cleaned.append(HumanMessage(content=new_parts))
        else:
            cleaned.append(msg)
    return cleaned


def _trim_history(history: list) -> list:
    """Keep only last 2 complete turns from history"""
    human_indices = [i for i, m in enumerate(history) if isinstance(m, HumanMessage)]
    if len(human_indices) > 2:
        history = history[human_indices[-2]:]
        logger.info(f"✂️ Trimmed history to last 2 turns ({len(history)} messages)")
    return _strip_images_from_history(history)


def _clean_text(text: str) -> str:
    """Remove model tokens and reasoning blocks"""
    text = re.sub(r'<\|im_end\|>|<\|im_start\|>\w*', '', text)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'^(thought|Thought)\s*\n', '', text.lstrip())
    return text.lstrip()


class UnifiedAgent:
    def __init__(self):
        self.llm = None
        self.llm_with_tools = None
        self.agent = None
        self.memory = memory
        self.tools = [
            log_expense,
            log_sales,
            calculate_profit,
            check_balance,
            save_to_wallet,
            request_send_money,
            confirm_send_money,
            verify_message
        ]

    async def initialize(self):
        logger.info("💰 Initializing SabiSpend Money Assistant")

        # Load AI configuration from environment
        ai_api_key = os.getenv("AI_API_KEY", "")
        ai_base_url = os.getenv("AI_BASE_URL", "")
        ai_model = os.getenv("AI_MODEL", "")

        self.llm = ChatOpenAI(
            base_url=ai_base_url,
            api_key=ai_api_key,
            model=ai_model,
            temperature=0.1,
            streaming=True,
            tags=["sabispend_money_assistant"],
            stop=["<|eot_id|>"],
        )

        logger.info(f"✅ AI Model configured: {ai_model}")

        self.llm_with_tools = self.llm.bind_tools(self.tools)

        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            checkpointer=self.memory,
        )

        logger.info("✅ SabiSpend agent initialized with 7 tools")

    def _load_history(self, config: dict) -> list:
        """Load and trim message history from checkpoint"""
        try:
            state = self.agent.get_state(config)
            history = state.values.get("messages", []) if state and state.values else []
            return _trim_history(list(history))
        except Exception as e:
            logger.warning(f"⚠️ Could not load history: {e}")
            return []

    def _save_to_checkpoint(self, config: dict, new_messages: list):
        """Append new messages to checkpoint"""
        try:
            self.agent.update_state(config, {"messages": new_messages})
            logger.info(f"💾 Saved {len(new_messages)} messages to checkpoint")
        except Exception as e:
            logger.error(f"❌ Checkpoint save failed: {e}")

    async def _execute_tools(self, tool_calls: list) -> list:
        """Execute all tool calls and return ToolMessages"""
        results = []
        for tc in tool_calls:
            name = tc.get("name", "")
            args = tc.get("args", {})
            tc_id = tc.get("id", "unknown")
            logger.info(f"🔧 Executing tool: {name}({args})")
            try:
                if name == "log_expense":
                    result = await log_expense.ainvoke(args)
                elif name == "log_sales":
                    result = await log_sales.ainvoke(args)
                elif name == "calculate_profit":
                    result = await calculate_profit.ainvoke(args)
                elif name == "check_balance":
                    result = await check_balance.ainvoke(args)
                elif name == "save_to_wallet":
                    result = await save_to_wallet.ainvoke(args)
                elif name == "verify_message":
                    result = await verify_message.ainvoke(args)
                else:
                    result = f"Unknown tool: {name}"
            except Exception as e:
                result = f"Tool error: {e}"
                logger.error(f"❌ Tool error: {e}")
            results.append(ToolMessage(content=result, tool_call_id=tc_id))
        return results

    async def get_response(
        self, content, thread_id: str, user_name: str = "there",
        message_type: str = "text", language: str = "english",
        original_content: str = None
    ) -> str:
        """
        Get response from SabiSpend agent (non-streaming)
        
        Args:
            content: User message (text or multipart with image)
            thread_id: User phone number
            user_name: User display name
            message_type: "text" or "voice"
            language: "english", "hausa", "igbo", "yoruba", "pidgin"
            original_content: Original message before translation
        """
        global _current_phone_number, _current_user_name
        _current_phone_number = thread_id
        _current_user_name = user_name
        
        if not self.agent:
            await self.initialize()

        # Handle different content types
        is_image = isinstance(content, list) and any(
            isinstance(p, dict) and p.get("type") == "image_url" for p in content
        )

        if is_image:
            text_content = next(
                (p["text"] for p in content if isinstance(p, dict) and p.get("type") == "text"),
                "[invoice/receipt image]"
            )
        elif isinstance(content, list):
            text_content = next(
                (p["text"] for p in content if isinstance(p, dict) and p.get("type") == "text"),
                str(content)
            )
        else:
            text_content = str(content)

        # Check for prompt injection
        if is_prompt_injection_attempt(text_content):
            return "Sorry! I only help with business money management."

        config = {"configurable": {"thread_id": thread_id}}

        is_voice = message_type == "voice"
        logger.info(f"💬 Mode: {'🎙️ VOICE' if is_voice else '⌨️ TEXT'} | Language: {language}")

        # Gemma handles all supported languages. Prompts differ only by medium.
        prompt = SABISPEND_VOICE_SYSTEM_PROMPT if is_voice else SABISPEND_SYSTEM_PROMPT
        prompt += f"\n\nThe user's selected language is {language or 'english'}. Reply only in that language."

        # Format user message
        if is_image:
            user_message = content
        else:
            user_message = f"[Voice Message in {language}]: {text_content}" if is_voice else text_content

        history = self._load_history(config)
        human_msg = HumanMessage(content=user_message)
        system_msg = SystemMessage(content=prompt)
        messages = [system_msg] + history + [human_msg]

        logger.info("🤖 Step 1: LLM call with tools")
        try:
            ai_response = await self.llm_with_tools.ainvoke(messages)
        except Exception as e:
            logger.error(f"❌ LLM error: {e}")
            return "I am currently not available, please try again later."

        new_checkpoint_msgs = [human_msg]

        # Handle tool calls
        if ai_response.tool_calls:
            logger.info(f"✅ Tool call: {[tc['name'] for tc in ai_response.tool_calls]}")
            new_checkpoint_msgs.append(ai_response)

            tool_results = await self._execute_tools(ai_response.tool_calls)
            new_checkpoint_msgs.extend(tool_results)

            logger.info("🤖 Step 2: Final LLM call without tools")
            final_messages = messages + [ai_response] + tool_results + [
                SystemMessage(content="You have the data above. Now write your final response to the user. Do NOT call any tool.")
            ]
        else:
            logger.info("ℹ️ No tool call — LLM answering directly")
            final_messages = messages

        try:
            final_response = await self.llm.ainvoke(final_messages)
            response = final_response.content if hasattr(final_response, "content") else str(final_response)
        except Exception as e:
            logger.error(f"❌ Final LLM error: {e}")
            return "I am currently not available, please try again later."

        if not response.strip():
            return "How else can I help you?"

        if contains_system_prompt_leak(response):
            return "I only help with business money management."

        response = _clean_text(response)

        # Save to checkpoint
        new_checkpoint_msgs.append(AIMessage(content=response))
        self._save_to_checkpoint(config, new_checkpoint_msgs)

        return response

    async def get_response_stream(self, **kwargs):
        """Compatibility streaming interface used by the WhatsApp TTS pipeline.

        Tool execution is completed before text is yielded, preventing speech from
        announcing an operation before its tool result is known.
        """
        response = await self.get_response(**kwargs)
        for part in re.split(r"(?<=[.!?])\s+", response):
            if part:
                yield part + (" " if not part.endswith("\n") else "")


# Global agent instance
unified_agent = UnifiedAgent()