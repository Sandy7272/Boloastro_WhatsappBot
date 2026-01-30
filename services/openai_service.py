import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_astrology_answer(question, astro_data, language="en"):
    """
    Uses OpenAI to answer user questions based on the fetched Prokerala data.
    """
    try:
        # Simplify data to save tokens
        planets_summary = []
        if astro_data.get("planets"):
            for p in astro_data["planets"]:
                planets_summary.append(f"{p['name']} in {p.get('rasi', {}).get('name')}")
        
        dosha_status = astro_data.get("dosha", {}).get("has_mangal_dosha", "Unknown")
        description = astro_data.get("dosha", {}).get("description", "")

        # Construct Prompt
        context = (
            f"Planetary Positions: {', '.join(planets_summary)}. "
            f"Mangal Dosha: {dosha_status}. {description}"
        )

        prompt = f"""
        You are an expert Vedic Astrologer.
        
        User's Chart Context:
        {context}
        
        User Question: "{question}"
        
        Instructions:
        1. Answer directly based on the chart context provided.
        2. Be empathetic, positive, and concise (under 100 words).
        3. Respond in the user's preferred language: {language}.
        """

        response = client.chat.completions.create(
            model="gpt-4o", # Or gpt-3.5-turbo
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250
        )
        
        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"OpenAI Error: {e}")
        return "I am having trouble reading the stars right now. Please try again later."