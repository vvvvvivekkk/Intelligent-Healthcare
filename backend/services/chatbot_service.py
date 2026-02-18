import os
import json
import time
import uuid
import logging
import requests
from backend.utils.database import query_db, execute_db
from backend.services.local_ai_fallback import generate_fallback_response

logger = logging.getLogger(__name__)

MEDICAL_DISCLAIMER = (
    "\n\n⚠️ **Disclaimer:** This is for informational purposes only. "
    "Please consult a licensed medical professional for proper diagnosis and treatment."
)


class ChatbotService:
    """Service layer for AI chatbot operations."""

    SYSTEM_PROMPT = """You are MedSync AI, a friendly AI assistant on the MedSync healthcare platform.

You can answer questions on ANY topic — technology, science, career, general knowledge, casual chat, etc.
You are NOT limited to health topics. Be helpful, intelligent, and adaptable.

WHEN RESPONDING TO HEALTH-RELATED QUESTIONS, follow this exact structure:

1. Start with ONE empathetic sentence (e.g. "I'm sorry you're not feeling well. 😟").
2. Mention 3–4 common possible causes — keep it brief.
3. Give simple home care advice (hydration, rest, basic OTC guidance).
4. Mention 2–3 red flag symptoms that need immediate medical attention.
5. Add a short disclaimer: "This is for informational purposes only and not medical advice."
6. End by asking:
   - ONE follow-up symptom question, AND
   - Whether the user would like to book an appointment related to this issue.

STRICT HEALTH RESPONSE RULES:
- Keep the entire response under 180 words.
- Do NOT use markdown headings (no #, ##, ###).
- Do NOT sound like a medical article or textbook.
- Sound like a helpful, caring assistant — calm, supportive, and conversational.
- Use relevant emojis throughout your response to make it warm and friendly (e.g. 😟💧🤒⚠️📋).
- Do NOT include any JSON, code blocks, or structured data.
- Never provide a final diagnosis or prescribe specific medications.
- If a specific medical specialist is recommended, append this tag at the very end: [[RECOMMEND: <Specialization_Name>]] (use the field name, e.g., [[RECOMMEND: Dermatology]], [[RECOMMEND: Cardiology]]).

SPECIAL RULES FOR APPOINTMENT BOOKING:
- If the user wants to book an appointment, ask for any missing details:
  1. Full Name
  2. Phone Number
  3. Doctor or Specialization
  4. Preferred Date
  5. Preferred Time
- Once all details are confirmed, respond with this structured format:
APPOINTMENT_BOOKING:
Name: <name>
Phone: <phone>
Doctor/Specialization: <doctor>
Date: <date>
Time: <time>

FOR NON-HEALTH QUESTIONS:
- Just answer helpfully and directly.
- Use bold text and lists where helpful, but keep it concise."""

    @staticmethod
    def get_or_create_session(user_id):
        """Get existing session or create new one."""
        recent = query_db(
            '''SELECT DISTINCT session_id FROM chat_history 
               WHERE user_id = ? ORDER BY created_at DESC LIMIT 1''',
            (user_id,), one=True
        )
        if recent:
            return recent['session_id']
        return f"sess-{uuid.uuid4().hex[:12]}"

    @staticmethod
    def create_new_session():
        """Create a new chat session ID."""
        return f"sess-{uuid.uuid4().hex[:12]}"

    @staticmethod
    def save_message(user_id, session_id, role, message, metadata=None):
        """Save a chat message to the database."""
        meta_json = json.dumps(metadata) if metadata else None
        execute_db(
            '''INSERT INTO chat_history (user_id, session_id, role, message, metadata)
               VALUES (?, ?, ?, ?, ?)''',
            (user_id, session_id, role, message, meta_json)
        )

    @staticmethod
    def get_chat_history(user_id, session_id=None, limit=50):
        """Get chat history for a user."""
        # Get latest N messages
        if session_id:
            query = '''SELECT * FROM chat_history WHERE user_id = ? AND session_id = ?
                       ORDER BY created_at DESC LIMIT ?'''
            args = (user_id, session_id, limit)
        else:
            query = '''SELECT * FROM chat_history WHERE user_id = ?
                       ORDER BY created_at DESC LIMIT ?'''
            args = (user_id, limit)
            
        messages = query_db(query, args)
        
        # Convert to dict and reverse to restore chronological order (ASC)
        results = [dict(m) for m in messages]
        results.reverse()
        return results

    @staticmethod
    def get_all_sessions(user_id):
        """Get all chat sessions for a user."""
        sessions = query_db(
            '''SELECT session_id, MIN(created_at) as started_at, 
               MAX(created_at) as last_message, COUNT(*) as message_count
               FROM chat_history WHERE user_id = ?
               GROUP BY session_id ORDER BY last_message DESC''',
            (user_id,)
        )
        return [dict(s) for s in sessions]

    @staticmethod
    def call_openrouter(messages, max_retries=2, retry_delay=1):
        """
        Call OpenRouter API with retry logic and automatic model fallback.
        
        Strategy:
        - Primary model: OPENROUTER_MODEL from .env (mistralai/mistral-7b-instruct)
        - Fallback model: OPENROUTER_FALLBACK_MODEL from .env (meta-llama/llama-3-8b-instruct)
        - On 429 (rate limit) or failure → retry with fallback model
        - On 401/403 (auth error) → fail immediately
        - max_tokens: 500 (reduced for efficiency)
        - temperature: 0.7 (balanced creativity)
        """
        api_key = os.getenv('OPENROUTER_API_KEY', '')
        primary_model = os.getenv('OPENROUTER_MODEL', 'mistralai/mistral-7b-instruct')
        fallback_model = os.getenv('OPENROUTER_FALLBACK_MODEL', 'meta-llama/llama-3-8b-instruct')
        base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        
        if not api_key or api_key == 'your_openrouter_api_key_here':
            return None, 'OpenRouter API key not configured'

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://medsync-ai.com',
            'X-Title': 'MedSync AI Healthcare Platform'
        }

        url = f"{base_url.rstrip('/')}/chat/completions"

        # Models to try in order: primary first, then fallback
        models_to_try = [primary_model]
        if fallback_model and fallback_model != primary_model:
            models_to_try.append(fallback_model)

        last_error = None

        for model in models_to_try:
            payload = {
                'model': model,
                'messages': messages,
                'temperature': 0.7,
                'max_tokens': 500
            }

            for attempt in range(max_retries):
                try:
                    logger.info(f"Calling OpenRouter with model={model}, attempt={attempt + 1}")
                    response = requests.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=30
                    )

                    if response.status_code == 200:
                        data = response.json()
                        content = data['choices'][0]['message']['content']
                        if model != primary_model:
                            logger.info(f"Success with fallback model: {model}")
                        return content, None
                    
                    # Auth errors - do not retry, do not fallback
                    if response.status_code in (401, 403):
                        logger.error(f"OpenRouter Auth Error: {response.text}")
                        return None, 'Invalid API Key or Permissions'

                    # Rate limited (429) - skip to fallback model immediately
                    if response.status_code == 429:
                        logger.warning(f"Model {model} rate-limited (429), switching to fallback...")
                        last_error = f'Rate limited on {model}'
                        break  # break retry loop, try next model

                    # Other errors - retry
                    last_error = f'HTTP {response.status_code}: {response.text[:200]}'
                    logger.warning(f"OpenRouter attempt {attempt + 1} with {model} failed: {last_error}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)

                except requests.exceptions.Timeout:
                    last_error = f'Timeout on {model}'
                    logger.warning(f"OpenRouter timeout (attempt {attempt + 1}) with {model}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                except requests.exceptions.ConnectionError:
                    last_error = 'Connection error'
                    logger.warning(f"OpenRouter connection error (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                except Exception as e:
                    last_error = str(e)
                    logger.error(f"OpenRouter unexpected error: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)

        return None, f'AI service unavailable ({last_error})'

    @staticmethod
    def process_message(user_id, session_id, user_message):
        """Process a user message and get AI response."""
        # Save user message
        ChatbotService.save_message(user_id, session_id, 'user', user_message)

        # Build conversation context — only last 8 messages to reduce token usage
        # Full history is still stored in DB; we only trim what goes to the API
        history = ChatbotService.get_chat_history(user_id, session_id, limit=8)
        
        messages = [{'role': 'system', 'content': ChatbotService.SYSTEM_PROMPT}]
        
        for msg in history:
            role = msg['role']
            if role == 'user':
                messages.append({'role': 'user', 'content': msg['message']})
            elif role == 'assistant':
                messages.append({'role': 'assistant', 'content': msg['message']})

        # Try OpenRouter AI first
        ai_response, error = ChatbotService.call_openrouter(messages)
        
        if error:
            # OpenRouter failed — use local fallback symptom analyzer
            logger.warning(f"OpenRouter unavailable ({error}), using local fallback")
            fallback_response, parsed_data = generate_fallback_response(user_message)
            
            # Save and return the local response
            ChatbotService.save_message(
                user_id, session_id, 'assistant', fallback_response,
                parsed_data
            )
            return fallback_response, parsed_data, None

        # Parse for structured JSON response
        parsed_data = ChatbotService.parse_ai_response(ai_response)
        
        # Strip the raw JSON block from the display text
        clean_response = ai_response
        if parsed_data:
            clean_response = ChatbotService.strip_json_block(ai_response)
            clean_response = clean_response + MEDICAL_DISCLAIMER
        else:
            # Check for [[RECOMMEND: ...]] tag
            import re
            match = re.search(r'\[\[RECOMMEND:\s*(.*?)\]\]', ai_response)
            if match:
                specialization = match.group(1).strip()
                # Create a minimal parsed_data object to trigger doctor recommendations
                parsed_data = {'recommended_specialization': specialization}
                # Remove the tag from the displayed response
                clean_response = re.sub(r'\[\[RECOMMEND:\s*.*?\]\]', '', ai_response).strip()

        # Save AI response
        metadata = parsed_data if parsed_data else None
        ChatbotService.save_message(user_id, session_id, 'assistant', clean_response, metadata)
        
        return clean_response, parsed_data, None

    @staticmethod
    def parse_ai_response(response):
        """Parse AI response for structured JSON data."""
        try:
            # Try to extract JSON block from response
            if '```json' in response:
                json_start = response.index('```json') + 7
                json_end = response.index('```', json_start)
                json_str = response[json_start:json_end].strip()
            elif '{' in response and '}' in response:
                # Try to find JSON object in response
                start = response.index('{')
                end = response.rindex('}') + 1
                json_str = response[start:end]
            else:
                return None

            data = json.loads(json_str)
            
            # Validate expected structure (confidence_level removed — not needed)
            expected_keys = ['possible_diseases',
                           'recommended_specialization', 'basic_advice']
            if all(key in data for key in expected_keys):
                # Drop confidence_level if present
                data.pop('confidence_level', None)
                return data
            return None
        except (json.JSONDecodeError, ValueError):
            return None

    @staticmethod
    def strip_json_block(text):
        """Remove JSON code blocks and raw JSON from response text."""
        import re
        # 1. Remove fenced ```json ... ``` blocks (greedy across newlines)
        cleaned = re.sub(r'```(?:json)?\s*\n?[\s\S]*?```', '', text)
        # 2. Remove any remaining raw JSON objects ({ ... } spanning multiple lines)
        cleaned = re.sub(r'\{[\s\S]*?"possible_diseases"[\s\S]*?\}', '', cleaned)
        cleaned = re.sub(r'\{[\s\S]*?"recommended_specialization"[\s\S]*?\}', '', cleaned)
        # 3. Clean up extra blank lines left behind
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
        return cleaned
