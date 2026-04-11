import asyncio
import random
import time
import tracemalloc

import telebot.types

from config import config_bot
from collections import defaultdict
from database import Session
from database.models import User, Word, UserWordAssociation
from sqlalchemy import and_
from utils import get_any_random_words, send_next_word_for_learn, send_next_word, set_learning_status
from telebot.async_telebot import AsyncTeleBot
from menus import main_menu, select_mode_lang_write, select_mode, select_mode_lang_button

tracemalloc.start()

bot = AsyncTeleBot(token=config_bot.bot_token, parse_mode="HTML")


# Словарь для хранения состояния повторения слов для каждого пользователя
user_repeat_state = defaultdict(dict)
user_learn_state = defaultdict(dict)


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
                learning_status="unlearned"
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
    # Получаем первое слово для изучения или добавления в изученные
    word_for_learn = get_any_random_words(howmuch=1,
                                          user_id=user_id,
                                          learning_status_for_request="unlearned")
    # Создаем словарь для хранения слов для изучения
    user_learn_state[user_id] = {
        "words": word_for_learn
    }
    await send_next_word_for_learn(bot=bot,
                                   chat_id=call.message.chat.id,
                                   message_id=call.message.message_id,
                                   user_id=user_id,
                                   user_learn_state=user_learn_state)


@bot.callback_query_handler(func=lambda call: call.data == "already_known")
async def already_known_word(call):
    await bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    # Получаем текущее слово
    current_word = user_learn_state[user_id].get("words")
    # Вызываем функцию добавляющую слово в изученные
    success = set_learning_status(word_for_learn=current_word,
                                  user_id=user_id,
                                  set_status="learned")
    if success:
        word_eng = current_word[0].get("word_eng")
        await bot.edit_message_text(f"✅ <b>{word_eng}</b> добавлено в словарь изученных слов",
                                    call.message.chat.id,
                                    call.message.message_id)
    else:
        await bot.edit_message_text("⚠️ Не удалось обновить статус слова",
                                    call.message.chat.id,
                                    call.message.message_id)
    # Очищаем список изучения
    del user_learn_state[user_id]
    # Получаем новое слово для изучения
    word_for_learn = get_any_random_words(howmuch=1, user_id=user_id, learning_status_for_request="unlearned")
    # Создаем словарь для хранения слов для изучения
    user_learn_state[user_id] = {
        "words": word_for_learn
    }
    # Вызываем функцию для отправки следующего слова
    await send_next_word_for_learn(bot=bot,
                                   chat_id=call.message.chat.id,
                                   message_id=call.message.message_id,
                                   user_id=user_id,
                                   user_learn_state=user_learn_state)


@bot.callback_query_handler(func=lambda call: call.data == "will_learn")
async def will_learn_word(call):
    await bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    word_for_learn = get_any_random_words(howmuch=1,
                                          user_id=user_id,
                                          learning_status_for_request="unlearned")
    user_learn_state[user_id]["words"].append(word_for_learn[0])
    print(user_learn_state[user_id]["words"])
    await bot.send_message(call.message.chat.id, "Will learned")
    await send_next_word_for_learn(bot=bot,
                                   chat_id=call.message.chat.id,
                                   message_id=call.message.message_id,
                                   user_id=user_id,
                                   user_learn_state=user_learn_state)



@bot.callback_query_handler(func=lambda call: call.data=="repeat_words")
async def repeat_words(call):
    await bot.answer_callback_query(call.id)
    await select_mode(bot, call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data=="write_mode")
async def select_mode_language_write(call):
    await bot.answer_callback_query(call.id)
    await select_mode_lang_write(bot, call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data=="button_mode")
async def select_mode_language_button(call):
    await bot.answer_callback_query(call.id)
    await select_mode_lang_button(bot, call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "rus_eng_button")
async def repeat_words_ru_eng_button(call):
    await bot.answer_callback_query(call.id)

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Начать", callback_data="start_rus_eng_button")
    button_2 = telebot.types.InlineKeyboardButton("Назад", callback_data="back:select_mode_lang")
    button_3 = telebot.types.InlineKeyboardButton("Главное меню", callback_data="back:show_main_menu")

    markup.add(button_1, button_2, button_3)

    await bot.edit_message_text("Выбран режим: RU-ENG",
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            reply_markup=markup
                              )


@bot.callback_query_handler(func=lambda call: call.data == "start_rus_eng_button")
async def start_rus_eng_button(call):
    await bot.answer_callback_query(call.id)
    user_id = call.from_user.id

    # Получаем слова для повторения
    words_for_repeat = get_any_random_words(howmuch=10,
                                            user_id=user_id,
                                            learning_status_for_request="learned")

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
        "mode": "button",
        "mode_lang": "rus_eng",
        "current_answer": None
        }

    await send_next_word(bot=bot,
                         chat_id=call.message.chat.id,
                         user_id=user_id,
                         user_repeat_state=user_repeat_state,
                         message_id=call.message.message_id,
                         )


@bot.callback_query_handler(func=lambda call: call.data == "eng_rus_button")
async def repeat_words_ru_eng_button(call):
    await bot.answer_callback_query(call.id)

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Начать", callback_data="start_eng_rus_button")
    button_2 = telebot.types.InlineKeyboardButton("Назад", callback_data="back:select_mode_lang")
    button_3 = telebot.types.InlineKeyboardButton("Главное меню", callback_data="back:show_main_menu")

    markup.add(button_1, button_2, button_3)

    await bot.edit_message_text("Выбран режим: ENG-RU",
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            reply_markup=markup
                              )


@bot.callback_query_handler(func=lambda call: call.data == "start_eng_rus_button")
async def start_eng_rus_button(call):
    await bot.answer_callback_query(call.id)
    user_id = call.from_user.id

    # Получаем слова для повторения
    words_for_repeat = get_any_random_words(howmuch=10,
                                            user_id=user_id,
                                            learning_status_for_request="learned")

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
        "mode": "button",
        "mode_lang": "eng_rus",
        "current_answer": None
        }

    await send_next_word(bot=bot,
                         chat_id=call.message.chat.id,
                         user_id=user_id,
                         user_repeat_state=user_repeat_state,
                         message_id=call.message.message_id,
                         )


@bot.callback_query_handler(func=lambda call: call.data.startswith("ans_but:"))
async def handler_answer_button(call):
    # Обработка ответов с кнопок
    await bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    # Проверяем, есть ли активный цикл у пользователя
    if user_id not in user_repeat_state:
        return

    user_state = user_repeat_state[user_id]
    user_answer = call.data.split(":")[-1]
    correct_answer = user_state["current_answer"]
    words = user_state["words"][user_state["current_index"]]
    mode_lang = user_state.get("mode_lang")
    # Выбирает слова для вывода исходя из режима
    current_word = words.get("word_eng") if mode_lang == "eng_rus" else words.get("word_rus")


    if user_answer == correct_answer:
        response_text = f"✅ Правильно! <b>{user_answer}</b> это <b>{current_word}</b>:"
        await bot.edit_message_text(text=response_text,
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id
                                    )
        user_state['current_index'] += 1
        await send_next_word(bot=bot,
                         chat_id=call.message.chat.id,
                         user_id=user_id,
                         user_repeat_state=user_repeat_state)
                         #message_id=call.message.message_id


    else:
        response_text = f"❌ Неверно! <b>{current_word}</b> это <b>{correct_answer}</b> Ваш ответ: {user_answer}"
        await bot.edit_message_text(text=response_text,
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id
                                    )
        user_state['current_index'] += 1
        await send_next_word(bot=bot,
                         chat_id=call.message.chat.id,
                         user_id=user_id,
                         user_repeat_state=user_repeat_state)
                         #message_id=call.message.message_id


@bot.callback_query_handler(func=lambda call: call.data == "rus_eng_write")
async def repeat_words_ru_eng_write(call):
    await bot.answer_callback_query(call.id)

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Начать", callback_data="start_rus_eng_write")
    button_2 = telebot.types.InlineKeyboardButton("Назад", callback_data="back:select_mode_lang")
    button_3 = telebot.types.InlineKeyboardButton("Главное меню", callback_data="back:show_main_menu")

    markup.add(button_1, button_2, button_3)

    await bot.edit_message_text("Выбран режим: RU-ENG",
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            reply_markup=markup
                              )


@bot.callback_query_handler(func=lambda call: call.data=="eng_rus_write")
async def repeat_words_eng_ru_write(call):
    await bot.answer_callback_query(call.id)

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Начать", callback_data="start_eng_rus_write")
    button_2 = telebot.types.InlineKeyboardButton("Назад", callback_data="back:select_mode_lang")
    button_3 = telebot.types.InlineKeyboardButton("Главное меню", callback_data="back:show_main_menu")

    markup.add(button_1, button_2, button_3)

    await bot.edit_message_text("Выбран режим: ENG-RU",
                          chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          reply_markup=markup
                          )


@bot.callback_query_handler(func=lambda call: call.data == "start_rus_eng_write")
async def start_rus_eng_write(call):
    await bot.answer_callback_query(call.id)
    user_id = call.from_user.id

    # Получаем слова для повторения
    words_for_repeat = get_any_random_words(howmuch=10,
                                            user_id=user_id,
                                            learning_status_for_request="learned")

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
        "mode": "write",
        "mode_lang": "rus_eng",
        "current_answer": None
    }
    # Отправляем первое слово
    await send_next_word(bot=bot,
                         chat_id=call.message.chat.id,
                         user_id=user_id,
                         user_repeat_state=user_repeat_state,
                         message_id=call.message.message_id)



@bot.callback_query_handler(func=lambda call: call.data == "start_eng_rus_write")
async def start_eng_rus_write(call):
    await bot.answer_callback_query(call.id)
    user_id = call.from_user.id

    # Получаем слова для повторения
    words_for_repeat = get_any_random_words(howmuch=10,
                                            user_id=user_id,
                                            learning_status_for_request="learned")

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
        "mode": "write",
        "mode_lang": "eng_rus",
        "current_answer": None
    }

    # Отправляем первое слово
    await send_next_word(bot=bot,
                         chat_id=call.message.chat.id,
                         user_id=user_id,
                         user_repeat_state=user_repeat_state,
                         message_id=call.message.message_id)


@bot.message_handler(func=lambda message: True)
async def handle_answer_write(message):
    # Обрабатывает текстовый ввод
    user_id = message.from_user.id

    # Проверяем, есть ли активный цикл у пользователя
    if user_id not in user_repeat_state:
        return

    state = user_repeat_state[user_id]
    user_answer = message.text.strip().lower()
    correct_answer = state['current_answer'].lower()
    mode_lang = state.get("mode_lang")
    words = state["words"][state["current_index"]]
    # Выбирает слова для вывода исходя из режима
    current_word = words.get("word_eng") if mode_lang == "eng_rus" else words.get("word_rus")
    # Проверяем ответ
    if user_answer == correct_answer:
        # Правильный ответ
        #await bot.delete_message(message.chat.id, message.message_id)
        response_text = f"✅ Правильно! <b>{user_answer}</b> это <b>{current_word}</b>:"
        await bot.send_message(message.chat.id, response_text)
        # await bot.edit_message_text(
        #     text=response_text,
        #     chat_id=message.chat.id,
        #     message_id=message.message_id - 1
        # )
        # Переходим к следующему слову
        state['current_index'] += 1
        await send_next_word(bot=bot,
                             chat_id=message.chat.id,
                             user_id=user_id,
                             user_repeat_state=user_repeat_state,
                             message=message)

    else:
        # Неправильный ответ
        #await bot.delete_message(message.chat.id, message.message_id)
        response_text = f"❌ Неверно! <b>{current_word}</b> это <b>{correct_answer}</b> Ваш ответ: {user_answer}"
        await bot.send_message(message.chat.id, response_text)
        # Переходим к следующему слову
        state['current_index'] += 1
        await send_next_word(bot=bot,
                             chat_id=message.chat.id,
                             user_id=user_id,
                             user_repeat_state=user_repeat_state,
                             message=message)


@bot.callback_query_handler(func=lambda call: call.data.startswith("back:"))
# Обработка кнопок навигации по меню
async def back(call):
    await bot.answer_callback_query(call.id)
    previous_state = call.data.split(":")[-1]
    if previous_state == "show_main_menu":
        await main_menu(bot, call.message.chat.id, call.message.message_id)
    elif previous_state == "select_mode":
        await select_mode(bot, call.message.chat.id, call.message.message_id)
    elif previous_state == "repeat_words":
        await select_mode(bot, call.message.chat.id, call.message.message_id)
    elif previous_state == "select_mode_lang":
        await select_mode_lang_write(bot, call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "user_stats")
async def user_stats(call):
    await bot.answer_callback_query(call.id)
    session = Session()
    user_name = call.from_user.first_name

    # количество выученных слов
    learned_words = session.query(UserWordAssociation).filter(
        and_(
            UserWordAssociation.user_id == call.from_user.id,
            UserWordAssociation.learning_status == "learned"
        )
    ).count()

    # количество невыученных слов
    unlearned_words = session.query(UserWordAssociation).filter(
        and_(
            UserWordAssociation.user_id == call.from_user.id,
            UserWordAssociation.learning_status == "unlearned"
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
