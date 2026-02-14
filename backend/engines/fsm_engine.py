"""
Enhanced FSM Engine - Final Version
Features:
- Smart date/time parsing (multiple formats)
- Complete Kundali Milan flow with Gun Milan
- Better user experience
- Multi-language support (6 languages)
"""

import logging
from datetime import datetime

from backend.engines.db_engine import (
    get_session, save_session, clear_session, get_or_create_user,
    log_message, log_question, grant_qna_pack, use_qna_credit,
    get_qna_credits, mark_kundali_purchased, has_kundali_access,
    mark_milan_purchased, has_milan_access
)

from backend.engines.astro_engine import get_kundali_cached
from backend.engines.ai_engine import ask_ai
from backend.engines.payment_engine import create_order, check_payment_status
from backend.engines.milan_engine import calculate_gun_milan, format_milan_report

from backend.utils.validators import valid_dob, valid_time, validate_place
from backend.engines.db_engine import log_message
from backend.utils.text_content import (
    WELCOME_MESSAGE, MAIN_MENU, LANGUAGE_MENU, ASTRO_SYSTEM_MENU,
    PAYMENT_MENU, QNA_MENU, HELP_MENU, PROGRESS_STEPS, ERROR_MESSAGES,
    SUCCESS_MESSAGES, PROMPTS, CONFIRMATION_TEMPLATE
)

logger = logging.getLogger(__name__)


# =========================
# GLOBAL COMMANDS
# =========================

GLOBAL_COMMANDS = {
    "START": ["start", "hi", "hello", "hey", "नमस्ते", "नमस्कार", "हॅलो"],
    "MENU": ["menu", "main menu", "home", "मेनू", "मुख्य मेनू"],
    "BACK": ["back", "← back", "previous", "पीछे", "मागे"],
    "CANCEL": ["cancel", "stop", "exit", "रद्द करें", "रद्द"],
    "HELP": ["help", "?", "मदद", "सहाय्य"],
    "LANGUAGE": ["lang", "language", "भाषा"]
}


# =========================
# HELPER FUNCTIONS
# =========================

def get_progress_bar(step, lang="EN", person=None):
    """Generate progress indicator with person name (for Milan)"""
    
    step_order = ["ASK_NAME", "ASK_DOB", "ASK_TIME", "ASK_PLACE"]
    
    if step not in step_order:
        return ""
    
    current = step_order.index(step) + 1
    total = len(step_order)
    
    filled = "●" * current
    empty = "○" * (total - current)
    
    step_text = PROGRESS_STEPS.get(lang, PROGRESS_STEPS["EN"])
    
    person_label = ""
    if person:
        labels = {
            "BOY": {"EN": " (Boy)", "HI": " (लड़का)", "MR": " (मुलगा)", "TA": " (ஆண்)", "TE": " (అబ్బాయి)", "BN": " (ছেলে)"},
            "GIRL": {"EN": " (Girl)", "HI": " (लड़की)", "MR": " (मुलगी)", "TA": " (பெண்)", "TE": " (అమ్మాయి)", "BN": " (মেয়ে)"}
        }
        person_label = labels.get(person, {}).get(lang, "")
    
    return f"\n[{filled}{empty}] {step_text} {current}/{total}{person_label}\n\n"


def is_global_command(msg):
    """Check if message is a global command"""
    msg_lower = msg.lower().strip()
    for cmd_type, keywords in GLOBAL_COMMANDS.items():
        if msg_lower in keywords:
            return cmd_type
    return None


def handle_global_command(phone, cmd_type, current_step, data):
    """Handle global commands"""
    lang = data.get("lang", "EN")
    
    if cmd_type == "START":
        reset(phone)
        return WELCOME_MESSAGE.get(lang, WELCOME_MESSAGE["EN"]) + "\n\n" + MAIN_MENU.get(lang, MAIN_MENU["EN"])
    
    if cmd_type == "MENU":
        save_session(phone, "MENU", data)
        return MAIN_MENU.get(lang, MAIN_MENU["EN"])
    
    if cmd_type == "HELP":
        return HELP_MENU.get(lang, HELP_MENU["EN"])
    
    if cmd_type == "LANGUAGE":
        save_session(phone, "LANG", data)
        return LANGUAGE_MENU
    
    if cmd_type == "CANCEL":
        clear_session(phone)
        return SUCCESS_MESSAGES["CANCELLED"].get(lang, SUCCESS_MESSAGES["CANCELLED"]["EN"])
    
    if cmd_type == "BACK":
        return handle_back(phone, current_step, data)
    
    return None


def handle_back(phone, current_step, data):
    """Handle BACK command"""
    lang = data.get("lang", "EN")
    
    back_map = {
        "ASK_DOB": "ASK_NAME",
        "ASK_TIME": "ASK_DOB",
        "ASK_PLACE": "ASK_TIME",
        "CONFIRM_DETAILS": "ASK_PLACE",
        
        # Milan specific
        "MILAN_GIRL_NAME": "MILAN_BOY_PLACE",
        "MILAN_GIRL_DOB": "MILAN_GIRL_NAME",
        "MILAN_GIRL_TIME": "MILAN_GIRL_DOB",
        "MILAN_GIRL_PLACE": "MILAN_GIRL_TIME",
        "MILAN_CONFIRM": "MILAN_GIRL_PLACE",
        
        "PAY_KUNDALI": "MENU",
        "PAY_QNA": "MENU",
        "PAY_MILAN": "MENU",
        "QNA": "MENU",
        "ASTRO_SYSTEM": "MENU",
        "LANG": "MENU"
    }
    
    previous_step = back_map.get(current_step)
    
    if not previous_step:
        return ERROR_MESSAGES["CANNOT_GO_BACK"].get(lang, ERROR_MESSAGES["CANNOT_GO_BACK"]["EN"])
    
    save_session(phone, previous_step, data)
    return get_step_prompt(previous_step, data, lang)


def get_step_prompt(step, data, lang):
    """Get prompt for a given step"""
    
    if step == "MENU":
        return MAIN_MENU.get(lang, MAIN_MENU["EN"])
    
    if step == "LANG":
        return LANGUAGE_MENU
    
    if step == "ASTRO_SYSTEM":
        return ASTRO_SYSTEM_MENU.get(lang, ASTRO_SYSTEM_MENU["EN"])
    
    if step in ["ASK_NAME", "ASK_DOB", "ASK_TIME", "ASK_PLACE"]:
        progress = get_progress_bar(step, lang)
        prompt = PROMPTS[step].get(lang, PROMPTS[step]["EN"])
        return progress + prompt
    
    # Milan steps
    if step in ["MILAN_GIRL_NAME", "MILAN_GIRL_DOB", "MILAN_GIRL_TIME", "MILAN_GIRL_PLACE"]:
        base_step = step.replace("MILAN_GIRL_", "ASK_")
        progress = get_progress_bar(base_step, lang, "GIRL")
        prompt = PROMPTS[base_step].get(lang, PROMPTS[base_step]["EN"])
        return progress + prompt
    
    return MAIN_MENU.get(lang, MAIN_MENU["EN"])


def format_confirmation_details(data, lang, person=None):
    """Format details for confirmation"""
    template = CONFIRMATION_TEMPLATE.get(lang, CONFIRMATION_TEMPLATE["EN"])
    
    if person == "BOY":
        return template.format(
            name=data.get("boy_name", "N/A"),
            dob=data.get("boy_dob", "N/A"),
            time=data.get("boy_time", "N/A"),
            place=data.get("boy_place", "N/A"),
            system=data.get("astro_system", "LAHIRI")
        )
    elif person == "GIRL":
        return template.format(
            name=data.get("girl_name", "N/A"),
            dob=data.get("girl_dob", "N/A"),
            time=data.get("girl_time", "N/A"),
            place=data.get("girl_place", "N/A"),
            system=data.get("astro_system", "LAHIRI")
        )
    else:
        return template.format(
            name=data.get("name", "N/A"),
            dob=data.get("dob", "N/A"),
            time=data.get("time", "N/A"),
            place=data.get("place", "N/A"),
            system=data.get("astro_system", "LAHIRI")
        )


def reset(phone):
    """Reset session"""
    save_session(phone, "MENU", {"lang": "EN", "preview_used": False})


# =========================
# MAIN FSM PROCESSOR
# =========================

def process_message(phone, msg):
    """Main message processor"""
    
    get_or_create_user(phone)
    log_message(phone, msg)
    
    msg = msg.strip()
    
    s = get_session(phone)
    
    if not s:
        reset(phone)
        s = get_session(phone)
    
    step = s["step"]
    data = s.get("data", {})
    lang = data.get("lang", "EN")
    
    # Global commands
    global_cmd = is_global_command(msg)
    if global_cmd:
        response = handle_global_command(phone, global_cmd, step, data)
        if response:
            return response
    
    # ================= MENU =================
    
    if step == "MENU":
        
        if msg == "1":
            data["mode"] = "KUNDALI"
            save_session(phone, "ASTRO_SYSTEM", data)
            return ASTRO_SYSTEM_MENU.get(lang, ASTRO_SYSTEM_MENU["EN"])
        
        if msg == "2":
            data["mode"] = "QNA"
            save_session(phone, "ASTRO_SYSTEM", data)
            return ASTRO_SYSTEM_MENU.get(lang, ASTRO_SYSTEM_MENU["EN"])
        
        if msg == "3":
            data["mode"] = "MILAN"
            save_session(phone, "ASTRO_SYSTEM", data)
            return ASTRO_SYSTEM_MENU.get(lang, ASTRO_SYSTEM_MENU["EN"])
        
        if msg == "4":
            save_session(phone, "LANG", data)
            return LANGUAGE_MENU
        
        if msg == "5":
            return HELP_MENU.get(lang, HELP_MENU["EN"])
        
        return ERROR_MESSAGES["INVALID_OPTION"].get(lang, ERROR_MESSAGES["INVALID_OPTION"]["EN"]) + "\n\n" + MAIN_MENU.get(lang, MAIN_MENU["EN"])
    
    # ================= ASTRO SYSTEM =================
    
    if step == "ASTRO_SYSTEM":
        
        if msg == "1":
            data["astro_system"] = "LAHIRI"
        elif msg == "2":
            data["astro_system"] = "KP"
        else:
            return ERROR_MESSAGES["INVALID_OPTION"].get(lang, ERROR_MESSAGES["INVALID_OPTION"]["EN"]) + "\n\n" + ASTRO_SYSTEM_MENU.get(lang, ASTRO_SYSTEM_MENU["EN"])
        
        # For Milan, we collect boy's details first
        if data.get("mode") == "MILAN":
            save_session(phone, "MILAN_BOY_NAME", data)
            progress = get_progress_bar("ASK_NAME", lang, "BOY")
            return progress + PROMPTS["ASK_NAME"].get(lang, PROMPTS["ASK_NAME"]["EN"])
        else:
            save_session(phone, "ASK_NAME", data)
            progress = get_progress_bar("ASK_NAME", lang)
            return progress + PROMPTS["ASK_NAME"].get(lang, PROMPTS["ASK_NAME"]["EN"])
    
    # ================= LANGUAGE =================
    
    if step == "LANG":
        
        language_map = {"1": "EN", "2": "HI", "3": "MR", "4": "TA", "5": "TE", "6": "BN"}
        selected_lang = language_map.get(msg)
        
        if not selected_lang:
            return ERROR_MESSAGES["INVALID_OPTION"].get(lang, ERROR_MESSAGES["INVALID_OPTION"]["EN"]) + "\n\n" + LANGUAGE_MENU
        
        data["lang"] = selected_lang
        save_session(phone, "MENU", data)
        
        return SUCCESS_MESSAGES["LANGUAGE_CHANGED"].get(selected_lang, SUCCESS_MESSAGES["LANGUAGE_CHANGED"]["EN"]) + "\n\n" + MAIN_MENU.get(selected_lang, MAIN_MENU["EN"])
    
    # ================= COLLECT DETAILS (KUNDALI/QNA) =================
    
    if step == "ASK_NAME":
        if len(msg) < 2:
            return ERROR_MESSAGES["NAME_TOO_SHORT"].get(lang, ERROR_MESSAGES["NAME_TOO_SHORT"]["EN"]) + "\n\n" + PROMPTS["ASK_NAME"].get(lang, PROMPTS["ASK_NAME"]["EN"])
        
        data["name"] = msg
        save_session(phone, "ASK_DOB", data)
        
        progress = get_progress_bar("ASK_DOB", lang)
        return progress + PROMPTS["ASK_DOB"].get(lang, PROMPTS["ASK_DOB"]["EN"])
    
    if step == "ASK_DOB":
        is_valid, error_msg, normalized = valid_dob(msg)
        
        if not is_valid:
            return error_msg.get(lang, error_msg.get("EN", "Invalid date")) + "\n\n" + PROMPTS["ASK_DOB"].get(lang, PROMPTS["ASK_DOB"]["EN"])
        
        data["dob"] = normalized
        save_session(phone, "ASK_TIME", data)
        
        progress = get_progress_bar("ASK_TIME", lang)
        return progress + PROMPTS["ASK_TIME"].get(lang, PROMPTS["ASK_TIME"]["EN"])
    
    if step == "ASK_TIME":
        is_valid, error_msg, normalized = valid_time(msg)
        
        if not is_valid:
            return error_msg.get(lang, error_msg.get("EN", "Invalid time")) + "\n\n" + PROMPTS["ASK_TIME"].get(lang, PROMPTS["ASK_TIME"]["EN"])
        
        data["time"] = normalized
        save_session(phone, "ASK_PLACE", data)
        
        progress = get_progress_bar("ASK_PLACE", lang)
        return progress + PROMPTS["ASK_PLACE"].get(lang, PROMPTS["ASK_PLACE"]["EN"])
    
    if step == "ASK_PLACE":
        data["place"] = msg
        
        logger.info(f"🔮 Generating kundali for {phone}: {msg}")
        kundali = get_kundali_cached(data)
        
        if not kundali:
            return ERROR_MESSAGES["PLACE_NOT_FOUND"].get(lang, ERROR_MESSAGES["PLACE_NOT_FOUND"]["EN"]) + "\n\n" + PROMPTS["ASK_PLACE"].get(lang, PROMPTS["ASK_PLACE"]["EN"])
        
        data["kundali"] = kundali
        save_session(phone, "CONFIRM_DETAILS", data)
        
        confirmation = format_confirmation_details(data, lang)
        return confirmation
    
    # ================= MILAN: BOY'S DETAILS =================
    
    if step == "MILAN_BOY_NAME":
        if len(msg) < 2:
            return ERROR_MESSAGES["NAME_TOO_SHORT"].get(lang, ERROR_MESSAGES["NAME_TOO_SHORT"]["EN"])
        
        data["boy_name"] = msg
        save_session(phone, "MILAN_BOY_DOB", data)
        
        progress = get_progress_bar("ASK_DOB", lang, "BOY")
        return progress + PROMPTS["ASK_DOB"].get(lang, PROMPTS["ASK_DOB"]["EN"])
    
    if step == "MILAN_BOY_DOB":
        is_valid, error_msg, normalized = valid_dob(msg)
        
        if not is_valid:
            return error_msg.get(lang, error_msg.get("EN", "Invalid date"))
        
        data["boy_dob"] = normalized
        save_session(phone, "MILAN_BOY_TIME", data)
        
        progress = get_progress_bar("ASK_TIME", lang, "BOY")
        return progress + PROMPTS["ASK_TIME"].get(lang, PROMPTS["ASK_TIME"]["EN"])
    
    if step == "MILAN_BOY_TIME":
        is_valid, error_msg, normalized = valid_time(msg)
        
        if not is_valid:
            return error_msg.get(lang, error_msg.get("EN", "Invalid time"))
        
        data["boy_time"] = normalized
        save_session(phone, "MILAN_BOY_PLACE", data)
        
        progress = get_progress_bar("ASK_PLACE", lang, "BOY")
        return progress + PROMPTS["ASK_PLACE"].get(lang, PROMPTS["ASK_PLACE"]["EN"])
    
    if step == "MILAN_BOY_PLACE":
        data["boy_place"] = msg
        
        # Generate boy's kundali
        boy_data = {
            "name": data["boy_name"],
            "dob": data["boy_dob"],
            "time": data["boy_time"],
            "place": data["boy_place"],
            "astro_system": data.get("astro_system", "LAHIRI")
        }
        
        boy_kundali = get_kundali_cached(boy_data)
        
        if not boy_kundali:
            return ERROR_MESSAGES["PLACE_NOT_FOUND"].get(lang, ERROR_MESSAGES["PLACE_NOT_FOUND"]["EN"])
        
        data["boy_kundali"] = boy_kundali
        
        # Now collect girl's details
        save_session(phone, "MILAN_GIRL_NAME", data)
        
        progress = get_progress_bar("ASK_NAME", lang, "GIRL")
        return "✅ Boy's details saved!\n\n" + progress + PROMPTS["ASK_NAME"].get(lang, PROMPTS["ASK_NAME"]["EN"])
    
    # ================= MILAN: GIRL'S DETAILS =================
    
    if step == "MILAN_GIRL_NAME":
        if len(msg) < 2:
            return ERROR_MESSAGES["NAME_TOO_SHORT"].get(lang, ERROR_MESSAGES["NAME_TOO_SHORT"]["EN"])
        
        data["girl_name"] = msg
        save_session(phone, "MILAN_GIRL_DOB", data)
        
        progress = get_progress_bar("ASK_DOB", lang, "GIRL")
        return progress + PROMPTS["ASK_DOB"].get(lang, PROMPTS["ASK_DOB"]["EN"])
    
    if step == "MILAN_GIRL_DOB":
        is_valid, error_msg, normalized = valid_dob(msg)
        
        if not is_valid:
            return error_msg.get(lang, error_msg.get("EN", "Invalid date"))
        
        data["girl_dob"] = normalized
        save_session(phone, "MILAN_GIRL_TIME", data)
        
        progress = get_progress_bar("ASK_TIME", lang, "GIRL")
        return progress + PROMPTS["ASK_TIME"].get(lang, PROMPTS["ASK_TIME"]["EN"])
    
    if step == "MILAN_GIRL_TIME":
        is_valid, error_msg, normalized = valid_time(msg)
        
        if not is_valid:
            return error_msg.get(lang, error_msg.get("EN", "Invalid time"))
        
        data["girl_time"] = normalized
        save_session(phone, "MILAN_GIRL_PLACE", data)
        
        progress = get_progress_bar("ASK_PLACE", lang, "GIRL")
        return progress + PROMPTS["ASK_PLACE"].get(lang, PROMPTS["ASK_PLACE"]["EN"])
    
    if step == "MILAN_GIRL_PLACE":
        data["girl_place"] = msg
        
        # Generate girl's kundali
        girl_data = {
            "name": data["girl_name"],
            "dob": data["girl_dob"],
            "time": data["girl_time"],
            "place": data["girl_place"],
            "astro_system": data.get("astro_system", "LAHIRI")
        }
        
        girl_kundali = get_kundali_cached(girl_data)
        
        if not girl_kundali:
            return ERROR_MESSAGES["PLACE_NOT_FOUND"].get(lang, ERROR_MESSAGES["PLACE_NOT_FOUND"]["EN"])
        
        data["girl_kundali"] = girl_kundali
        
        # Show both confirmations
        save_session(phone, "MILAN_CONFIRM", data)
        
        boy_confirm = format_confirmation_details(data, lang, "BOY")
        girl_confirm = format_confirmation_details(data, lang, "GIRL")
        
        return f"👦 *Boy's Details:*\n{boy_confirm}\n\n👧 *Girl's Details:*\n{girl_confirm}"
    
    # ================= MILAN CONFIRMATION =================
    
    if step == "MILAN_CONFIRM":
        
        if msg == "1":
            # Check if already purchased
            if has_milan_access(phone):
                # Calculate Gun Milan
                milan_result = calculate_gun_milan(data["boy_kundali"], data["girl_kundali"])
                
                if milan_result:
                    report = format_milan_report(milan_result, lang)
                    save_session(phone, "MENU", data)
                    return report + "\n\n" + MAIN_MENU.get(lang, MAIN_MENU["EN"])
                else:
                    return ERROR_MESSAGES["UNKNOWN_COMMAND"].get(lang, ERROR_MESSAGES["UNKNOWN_COMMAND"]["EN"])
            
            # Create payment order
            order_link = create_order(phone, "MILAN")
            
            if not order_link:
                return ERROR_MESSAGES["PAYMENT_SYSTEM_ERROR"].get(lang, ERROR_MESSAGES["PAYMENT_SYSTEM_ERROR"]["EN"])
            
            data["payment_link"] = order_link
            save_session(phone, "PAY_MILAN", data)
            
            return PAYMENT_MENU.get(lang, PAYMENT_MENU["EN"]).format(link=order_link)
        
        elif msg == "2":
            reset(phone)
            return SUCCESS_MESSAGES["STARTING_OVER"].get(lang, SUCCESS_MESSAGES["STARTING_OVER"]["EN"]) + "\n\n" + MAIN_MENU.get(lang, MAIN_MENU["EN"])
    
    # ================= CONFIRMATION (KUNDALI/QNA) =================
    
    if step == "CONFIRM_DETAILS":
        
        if msg == "1":
            mode = data.get("mode")
            
            if mode == "KUNDALI":
                if has_kundali_access(phone):
                    save_session(phone, "MENU", data)
                    return SUCCESS_MESSAGES["ALREADY_PURCHASED"].get(lang, SUCCESS_MESSAGES["ALREADY_PURCHASED"]["EN"]) + "\n\n" + MAIN_MENU.get(lang, MAIN_MENU["EN"])
                
                order_link = create_order(phone, "KUNDALI")
                
                if not order_link:
                    return ERROR_MESSAGES["PAYMENT_SYSTEM_ERROR"].get(lang, ERROR_MESSAGES["PAYMENT_SYSTEM_ERROR"]["EN"])
                
                data["payment_link"] = order_link
                save_session(phone, "PAY_KUNDALI", data)
                
                return PAYMENT_MENU.get(lang, PAYMENT_MENU["EN"]).format(link=order_link)
            
            elif mode == "QNA":
                save_session(phone, "QNA", data)
                return QNA_MENU["READY"].get(lang, QNA_MENU["READY"]["EN"])
        
        elif msg == "2":
            reset(phone)
            return SUCCESS_MESSAGES["STARTING_OVER"].get(lang, SUCCESS_MESSAGES["STARTING_OVER"]["EN"]) + "\n\n" + MAIN_MENU.get(lang, MAIN_MENU["EN"])
        
        else:
            confirmation = format_confirmation_details(data, lang)
            return ERROR_MESSAGES["INVALID_OPTION"].get(lang, ERROR_MESSAGES["INVALID_OPTION"]["EN"]) + "\n\n" + confirmation
    
    # ================= PAYMENTS =================
    
    if step == "PAY_KUNDALI":
        if check_payment_status(phone):
            mark_kundali_purchased(phone)
            save_session(phone, "MENU", data)
            return SUCCESS_MESSAGES["PAYMENT_SUCCESS"].get(lang, SUCCESS_MESSAGES["PAYMENT_SUCCESS"]["EN"]) + "\n\n" + MAIN_MENU.get(lang, MAIN_MENU["EN"])
        
        return PAYMENT_MENU.get(lang, PAYMENT_MENU["EN"]).format(link=data.get("payment_link", "#"))
    
    if step == "PAY_MILAN":
        if check_payment_status(phone):
            mark_milan_purchased(phone)
            
            # Calculate Gun Milan
            milan_result = calculate_gun_milan(data["boy_kundali"], data["girl_kundali"])
            
            if milan_result:
                report = format_milan_report(milan_result, lang)
                save_session(phone, "MENU", data)
                return "✅ Payment successful!\n\n" + report + "\n\n" + MAIN_MENU.get(lang, MAIN_MENU["EN"])
            else:
                return ERROR_MESSAGES["UNKNOWN_COMMAND"].get(lang, ERROR_MESSAGES["UNKNOWN_COMMAND"]["EN"])
        
        return PAYMENT_MENU.get(lang, PAYMENT_MENU["EN"]).format(link=data.get("payment_link", "#"))
    
    # ================= Q&A MODE =================
    
    if step == "QNA":
        credits = get_qna_credits(phone)
        
        if credits <= 0:
            if check_payment_status(phone):
                grant_qna_pack(phone, 4)
                credits = 4
            else:
                order_link = create_order(phone, "QNA")
                if not order_link:
                    return ERROR_MESSAGES["PAYMENT_SYSTEM_ERROR"].get(lang, ERROR_MESSAGES["PAYMENT_SYSTEM_ERROR"]["EN"])
                return PAYMENT_MENU.get(lang, PAYMENT_MENU["EN"]).format(link=order_link)
        
        use_qna_credit(phone)
        remaining = credits - 1
        
        log_question(phone, msg)
        
        logger.info(f"🤖 Processing Q&A for {phone}")
        answer = ask_ai(phone, msg, data)
        
        credits_text = QNA_MENU["REMAINING"].get(lang, QNA_MENU["REMAINING"]["EN"]).format(remaining=remaining)
        
        return answer + "\n\n" + credits_text + "\n\n" + QNA_MENU["CONTINUE"].get(lang, QNA_MENU["CONTINUE"]["EN"])
    
    # ================= FALLBACK =================
    
    logger.warning(f"⚠️ Unknown state '{step}' for user {phone}, resetting to menu")
    reset(phone)
    return ERROR_MESSAGES["UNKNOWN_COMMAND"].get(lang, ERROR_MESSAGES["UNKNOWN_COMMAND"]["EN"]) + "\n\n" + MAIN_MENU.get(lang, MAIN_MENU["EN"])