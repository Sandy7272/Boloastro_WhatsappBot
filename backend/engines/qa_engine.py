from services.openai_service import get_astrology_answer
import logging

logger = logging.getLogger(__name__)

def answer_question(question, session_data, language="en"):
    """
    Determines how to answer the question.
    """
    astro_data = session_data.get("astro_data")
    
    if not astro_data:
        return "⚠️ Error: Chart data missing. Please regenerate your Kundali."

    # Use AI to answer
    try:
        return get_astrology_answer(question, astro_data, language)
    except Exception as e:
        logger.error(f"QA Engine Error: {e}")
        return "I am having trouble connecting to the cosmic server."