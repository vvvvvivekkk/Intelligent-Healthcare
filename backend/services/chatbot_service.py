import os
import json
import time
import uuid
import logging
import requests
from backend.utils.database import query_db, execute_db

logger = logging.getLogger(__name__)

MEDICAL_DISCLAIMER = (
    "\n\n⚠️ **Medical Disclaimer:** This system provides decision support only. "
    "Please consult a licensed medical professional for proper diagnosis and treatment."
)


class ChatbotService:
    """Service layer for AI chatbot operations."""

    SYSTEM_PROMPT = """You are MedSync AI, an intelligent healthcare assistant. 
Your role is to:
1. Listen to patient symptoms carefully
2. Ask clarifying questions if needed
3. Provide a structured analysis when you have enough information

When the patient has described enough symptoms, respond with a JSON block in this exact format:
```json
{
    "possible_diseases": ["disease1", "disease2", "disease3"],
    "confidence_level": "high/medium/low",
    "recommended_specialization": "specialization name",
    "basic_advice": "brief health advice"
}
```

Important rules:
- Always be empathetic and professional
- Never diagnose definitively - only suggest possibilities
- Always recommend consulting a real doctor
- If symptoms are unclear, ask follow-up questions
- For emergencies (chest pain, difficulty breathing, severe bleeding), immediately advise calling emergency services
- Keep responses concise but informative
- When providing the JSON analysis, also include a human-readable explanation before the JSON block"""

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
        if session_id:
            messages = query_db(
                '''SELECT * FROM chat_history WHERE user_id = ? AND session_id = ?
                   ORDER BY created_at ASC LIMIT ?''',
                (user_id, session_id, limit)
            )
        else:
            messages = query_db(
                '''SELECT * FROM chat_history WHERE user_id = ?
                   ORDER BY created_at DESC LIMIT ?''',
                (user_id, limit)
            )
        return [dict(m) for m in messages]

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
    def call_openrouter(messages, max_retries=3, retry_delay=2):
        """Call OpenRouter API with retry logic."""
        api_key = os.getenv('OPENROUTER_API_KEY', '')
        if not api_key or api_key == 'your_openrouter_api_key_here':
            return None, 'OpenRouter API key not configured'

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://medsync-ai.com',
            'X-Title': 'MedSync AI Healthcare Platform'
        }

        payload = {
            'model': 'meta-llama/llama-3.3-70b-instruct:free',
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 1024
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data['choices'][0]['message']['content']
                    return content, None
                
                logger.warning(f"OpenRouter API attempt {attempt + 1} failed: {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))

            except requests.exceptions.Timeout:
                logger.warning(f"OpenRouter API timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
            except Exception as e:
                logger.error(f"OpenRouter API error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        return None, 'AI service temporarily unavailable. Please try again.'

    @staticmethod
    def process_message(user_id, session_id, user_message):
        """Process a user message and get AI response."""
        # Save user message
        ChatbotService.save_message(user_id, session_id, 'user', user_message)

        # Build conversation context
        history = ChatbotService.get_chat_history(user_id, session_id, limit=20)
        
        messages = [{'role': 'system', 'content': ChatbotService.SYSTEM_PROMPT}]
        
        for msg in history:
            role = msg['role']
            if role == 'user':
                messages.append({'role': 'user', 'content': msg['message']})
            elif role == 'assistant':
                messages.append({'role': 'assistant', 'content': msg['message']})

        # Call AI
        ai_response, error = ChatbotService.call_openrouter(messages)
        
        if error:
            fallback = ("I'm currently experiencing some technical difficulties. "
                       "Please try again in a moment. If you're experiencing a medical emergency, "
                       "please call your local emergency services immediately.")
            ChatbotService.save_message(user_id, session_id, 'assistant', fallback)
            return fallback, None, error

        # Parse for structured JSON response
        parsed_data = ChatbotService.parse_ai_response(ai_response)
        
        # Append disclaimer
        full_response = ai_response + MEDICAL_DISCLAIMER
        
        # Save AI response
        metadata = parsed_data if parsed_data else None
        ChatbotService.save_message(user_id, session_id, 'assistant', full_response, metadata)
        
        return full_response, parsed_data, None

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
            
            # Validate expected structure
            expected_keys = ['possible_diseases', 'confidence_level', 
                           'recommended_specialization', 'basic_advice']
            if all(key in data for key in expected_keys):
                return data
            return None
        except (json.JSONDecodeError, ValueError):
            return None
