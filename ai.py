import os
from openai import OpenAI
from config import config_bot

client = OpenAI(api_key=os.getenv(config_bot.openai_token))


def explain_with_examples(word: str) -> str:
    prompt = f"""
Ты помощник для изучения английского.

Для слова "{word}":
1. Дай перевод на русский
2. Приведи 2 простых предложения (A2 уровень)
3. Для каждого предложения дай перевод на русский


Формат ответа:

Слово: ...
Перевод: ...

Примеры:
1. ...
Перевод: ...

2. ...
Перевод: ...
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
    )

    return response.choices[0].message.content.strip()