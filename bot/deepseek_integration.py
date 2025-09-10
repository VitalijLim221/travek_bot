# bot/deepseek_integration.py
from openai import OpenAI
import json
from bot.config import DEEPSEEK_API_KEY

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://openrouter.ai/api/v1")
def load_prompt(filename):
    "Load prompt from file"
    try:
        with open(f"bot/prompts/{filename}", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def get_route_from_deepseek(interests: str, count: int):
    "Generate route using DeepSeek API"
    prompt_template = load_prompt("route_prompt.txt")
    if not prompt_template:
        # Fallback prompt
        prompt_template = """Создай маршрут в Минске, состоящий из {count} объектов, 
        подходящих под интересы: {interests}. Для каждого объекта укажи название, 
        краткое описание и координаты в формате JSON:
        [
          {{
            "name": "Название объекта",
            "description": "Краткое описание объекта",
            "latitude": 53.9045,
            "longitude": 27.5577
          }},
          ...
        ]
        Ответ должен содержать только JSON массив без дополнительного текста."""

    prompt = prompt_template.format(interests=interests, count=count)

    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[
                {"role": "system", "content": "Ты полезный помощник, который создает туристические маршруты."},
                {"role": "user", "content": prompt}
            ],
            stream=False,
            temperature=0.7,
            max_tokens=2000
        )

        content = response.choices[0].message.content.strip()

        # Try to extract JSON from response
        if content.startswith('```json'):
            content = content[7:]  # Remove ```json
        if content.endswith('```'):
            content = content[:-3]  # Remove ```

        # Parse JSON
        route_data = json.loads(content)
        return route_data

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response content: {content}")
        # Return fallback route
        return [
            {
                "name": "Минск",
                "description": "Столица Беларуси",
                "latitude": 53.9045,
                "longitude": 27.5577
            }
        ]
    except Exception as e:
        print(f"DeepSeek API error: {e}")
        # Return fallback route
        return [
            {
                "name": "Минск",
                "description": "Столица Беларуси",
                "latitude": 53.9045,
                "longitude": 27.5577
            }
        ]

def get_interests_suggestions(user_input: str):
    "Get interests suggestions using DeepSeek API"
    prompt_template = load_prompt("interests_prompt.txt")
    if not prompt_template:
        # Fallback prompt
        prompt_template = """Пользователь ввел интересы: "{input}". 
        Предложи 5 уточненных или связанных интересов в формате JSON массива строк:
        ["интерес1", "интерес2", ...]
        Ответ должен содержать только JSON массив без дополнительного текста."""

    prompt = prompt_template.format(input=user_input)

    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[
                {"role": "system", "content": "Ты полезный помощник, который уточняет интересы пользователя."},
                {"role": "user", "content": prompt}
            ],
            stream=False,
            temperature=0.7,
            max_tokens=500
        )

        content = response.choices[0].message.content.strip()

        # Try to extract JSON from response
        if content.startswith('```json'):
            content = content[7:]  # Remove ```json
        if content.endswith('```'):
            content = content[:-3]  # Remove ```

        # Parse JSON
        interests_list = json.loads(content)
        return interests_list

    except Exception as e:
        print(f"DeepSeek API error for interests: {e}")
        # Return original input as fallback
        return [user_input]