import asyncio
import time

import telebot.types

from config import config_bot
from collections import defaultdict
from database import Session
from database.models import User, Word, UserWordAssociation
from sqlalchemy import and_, lambda_stmt
from utils import get_any_random_words, get_three_random_word
from telebot.async_telebot import AsyncTeleBot
from menus import main_menu, select_mode, send_next_word

bot = AsyncTeleBot(token=config_bot.bot_token, parse_mode="HTML")


# Словарь для хранения состояния повторения слов для каждого пользователя
user_repeat_state = defaultdict(dict)


@bot.message_handler(commands=["start"])
async def send_start_message(message):
    user_id = message.from_user.id
    if user_id in user_repeat_state:
        del user_repeat_state[user_id]
    await main_menu(bot, message.chat.id)

    session = Session()

    try:
        user = session.get(User, user_id)
        if user:
            print("User already exists")
            return

        print("Create new user")
        # Создаем нового пользователя
        new_user = User(
            user_id=user_id,
            user_first_name=message.from_user.first_name
        )
        session.add(new_user)
        session.flush()

        # Получаем все слова из базы
        all_words = session.query(Word).all()

        # Добавляем в таблицу связи все слова как невыученные
        for word in all_words:
            association = UserWordAssociation(
                user_id=user_id,
                word_id=word.id,
                learned=False
            )
            session.add(association)

        session.commit()
        print(f"Created user and added {len(all_words)} words to learn")

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()


@bot.callback_query_handler(func=lambda call: call.data == "new_words")
async def new_words(call):
    await bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    words_for_learn = get_any_random_words(howmuch=5, user_id=user_id)
    for word in words_for_learn:
        await bot.send_message(call.message.chat.id, f"{word.get('word_eng')} - {word.get('word_rus')}")
    await main_menu(bot=bot, chat_id=call.message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data=="repeat_words")
async def repeat_words(call):
    await bot.answer_callback_query(call.id)
    await select_mode(bot,
                      call.message.chat.id,
                      call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "ru_eng")
async def repeat_words_ru_eng(call):
    await bot.answer_callback_query(call.id)

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Начать", callback_data="start_ru_eng")
    button_2 = telebot.types.InlineKeyboardButton("Назад", callback_data="back:select_mode")
    button_3 = telebot.types.InlineKeyboardButton("Главное меню", callback_data="back:show_main_menu")

    markup.add(button_1, button_2, button_3)

    await bot.edit_message_text("Выбран режим: RU-ENG",
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            reply_markup=markup
                              )


@bot.callback_query_handler(func=lambda call: call.data=="eng_ru")
async def repeat_words_eng_ru(call):
    await bot.answer_callback_query(call.id)

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Начать", callback_data="start_eng_ru")
    button_2 = telebot.types.InlineKeyboardButton("Назад", callback_data="back:select_mode")
    button_3 = telebot.types.InlineKeyboardButton("Главное меню", callback_data="back:show_main_menu")

    markup.add(button_1, button_2, button_3)

    await bot.edit_message_text("Выбран режим: ENG-RU",
                          chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          reply_markup=markup
                          )


@bot.callback_query_handler(func=lambda call: call.data == "start_ru_eng")
async def start_ru_eng_mode(call):
    await bot.answer_callback_query(call.id)
    user_id = call.from_user.id

    # Получаем слова для повторения
    words_for_repeat = get_any_random_words(howmuch=4,
                                            user_id=user_id,
                                            learned=True)

    if not words_for_repeat:
        text = "У Вас еще нет изученных слов"
        await bot.edit_message_text(
            text=text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        # Переход в главное меню
        await main_menu(bot=bot,
                        chat_id=call.message.chat.id)
        return

    # Сохраняем состояние пользователя
    user_repeat_state[user_id] = {
        "words": words_for_repeat,
        "current_index": 0,
        "mode": "ru_eng",
        "current_answer": None
    }
    # Отправляем первое слово
    await send_next_word(bot=bot,
                         chat_id=call.message.chat.id,
                         user_id=user_id,
                         user_repeat_state=user_repeat_state,
                         message_id=call.message.message_id)



@bot.message_handler(func=lambda message: True)
async def handle_answer(message):
    """Обрабатывает ответы пользователя в викторине"""
    user_id = message.from_user.id

    # Проверяем, есть ли активная викторина у пользователя
    if user_id not in user_repeat_state:
        return

    state = user_repeat_state[user_id]
    user_answer = message.text.strip().lower()
    correct_answer = state['current_answer'].lower()
    # Проверяем ответ
    if user_answer == correct_answer:
        # Правильный ответ
        response_text = f"✅ Правильно! Идем дальше:"
        await bot.send_message(message.chat.id, response_text)

        # Переходим к следующему слову
        state['current_index'] += 1
        await send_next_word(bot=bot,
                             chat_id=message.chat.id,
                             user_id=user_id,
                             user_repeat_state=user_repeat_state)

    else:
        # Неправильный ответ
        response_text = f"❌ Неверно! Правильный перевод: {correct_answer} Идем дальше:"
        await bot.send_message(message.chat.id, response_text)

        # Переходим к следующему слову
        state['current_index'] += 1
        await send_next_word(bot=bot,
                             chat_id=message.chat.id,
                             user_id=user_id,
                             user_repeat_state=user_repeat_state)

        #await bot.delete_message(message.chat.id, message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("back:"))
async def back(call):
    await bot.answer_callback_query(call.id)
    previous_state = call.data.split(":")[-1]
    if previous_state == "show_main_menu":
        await main_menu(bot, call.message.chat.id, call.message.message_id)
    elif previous_state == "select_mode":
        await select_mode(bot, call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "user_stats")
async def user_stats(call):
    await bot.answer_callback_query(call.id)
    session = Session()
    user_name = call.from_user.first_name

    # количество выученных слов
    learned_words = session.query(UserWordAssociation).filter(
        and_(
            UserWordAssociation.user_id == call.from_user.id,
            UserWordAssociation.learned == True
        )
    ).count()

    # количество невыученных слов
    unlearned_words = session.query(UserWordAssociation).filter(
        and_(
            UserWordAssociation.user_id == call.from_user.id,
            UserWordAssociation.learned == False
        )
    ).count()

    total_words = unlearned_words + learned_words
    learned_percent = round(learned_words / total_words * 100, 1)
    text = f"{user_name}, ты знаешь уже {learned_words} слов, это {learned_percent}%! Всего слов: {total_words} Осталось выучить {unlearned_words}"
    await bot.edit_message_text(
        text=text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id
    )
    session.close()

    await main_menu(bot=bot, chat_id=call.message.chat.id)

if __name__ == "__main__":
    asyncio.run(bot.polling(none_stop=True))
