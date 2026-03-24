import telebot.types
import time
import random
import threading
import pydoc

from config import config
from collections import defaultdict
from telebot import TeleBot
from database import Session
from database.models import User, Word, UserWordAssociation
from sqlalchemy import and_
from utils import get_five_random_words, get_three_random_word

bot = TeleBot(token=config.bot_token, parse_mode="HTML")

# Словарь для хранения состояния викторины для каждого пользователя
user_quiz_state = defaultdict(dict)


@bot.message_handler(commands=["start"])
def send_start_message(message):
    user_id = message.from_user.id

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Учим новые", callback_data="new_words")
    button_2 = telebot.types.InlineKeyboardButton("Повторяем старые", callback_data="repeat_words")
    button_3 = telebot.types.InlineKeyboardButton("Мои успехи", callback_data="user_stats")

    markup.add(button_1, button_2, button_3)

    bot.send_message(message.chat.id, f"Привет {message.from_user.first_name}, нажмите кнопку:", reply_markup=markup)

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
def new_words(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    words = get_five_random_words(user_id=user_id)
    bot.send_message(call.message.chat.id, "Здесь новые слова:")
    for word_dict in words:
        bot.send_message(call.message.chat.id,
                         f"<b>{word_dict.get('word_eng')}</b> - <i>{word_dict.get('word_rus')}</i>")
        #time.sleep(1)
        threading.Timer(0.5, ask_quiz_question, args=[user_id]).start()


    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Учим новые", callback_data="new_words")
    button_2 = telebot.types.InlineKeyboardButton("Повторяем старые", callback_data="repeat_words")
    button_3 = telebot.types.InlineKeyboardButton("Мои успехи", callback_data="user_stats")

    markup.add(button_1, button_2, button_3)

    bot.send_message(
        call.message.chat.id,
        "Что дальше?",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == "repeat_words")
def choice_mode_quiz(call):
    markup = telebot.types.InlineKeyboardMarkup()

    button_1 = telebot.types.InlineKeyboardButton("ENG -> RUS", callback_data="eng_rus")
    button_2 = telebot.types.InlineKeyboardButton("RUS -> ENG", callback_data="rus_eng")

    markup.add(button_1, button_2)

    bot.send_message(
        call.message.chat.id,
        "Выберете режим:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "rus_eng")
def repeat_words_rus_eng(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id

    # Получаем слова для викторины
    words = get_five_random_words(user_id=user_id, learned=True)

    if not words:
        bot.send_message(call.message.chat.id, "У вас нет изученных слов для повторения!")
        return

    # Инициализируем состояние викторины для пользователя
    user_quiz_state[user_id] = {
        'words': words,
        'current_index': 0,
        'correct_answers': 0,
        'total_words': len(words),
        'chat_id': call.message.chat.id,
        'start_message_id': call.message.message_id  # Сохраняем ID начального сообщения
    }

    # Запускаем первый вопрос
    ask_quiz_question(user_id)


def ask_quiz_question(user_id):
    """Задает следующий вопрос викторины"""
    quiz_data = user_quiz_state.get(user_id)

    # Проверяем, есть ли активная викторина
    if not quiz_data:
        return

    # Проверяем, не завершена ли викторина
    if quiz_data['current_index'] >= quiz_data['total_words']:
        finish_quiz(user_id)
        return

    # Получаем текущее слово
    word_dict = quiz_data['words'][quiz_data['current_index']]

    # Генерируем варианты ответов
    ans_var = get_three_random_word()
    # Добавляем верный вариант ответа
    ans_var.append(word_dict.get("word_eng"))
    random.shuffle(ans_var)

    # Сохраняем правильный ответ для проверки
    quiz_data['correct_answer'] = word_dict.get("word_rus")
    quiz_data['current_answers'] = ans_var  # Сохраняем варианты для текущего вопроса

    # Создаем клавиатуру с уникальными callback_data
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    buttons = []

    # Генерируем callback_data по индексу в списке
    for i, answer in enumerate(ans_var):
        # Формат: quiz_userId_questionIndex_answerIndex
        callback_data = f"quiz_{user_id}_{quiz_data['current_index']}_{i}"
        button = telebot.types.InlineKeyboardButton(answer, callback_data=callback_data)
        buttons.append(button)

    markup.add(*buttons)

    # Отправляем вопрос (не удаляем предыдущие сообщения)
    message = bot.send_message(
        quiz_data['chat_id'],
        f"Вопрос {quiz_data['current_index'] + 1}/{quiz_data['total_words']}\n"
        f"Выберите правильный вариант. <b>{word_dict.get('word_rus')}</b> это:",
        reply_markup=markup,
        parse_mode='HTML'
    )

    # Сохраняем ID сообщения с вопросом
    quiz_data['last_question_message_id'] = message.message_id


@bot.callback_query_handler(func=lambda call: call.data.startswith("quiz_"))
def handle_quiz_answer(call):
    bot.answer_callback_query(call.id)

    # Парсим callback_data
    parts = call.data.split("_")
    if len(parts) < 4:
        return

    user_id = int(parts[1])
    question_index = int(parts[2])
    answer_index = int(parts[3])

    # Проверяем, что ответ от того же пользователя
    if call.from_user.id != user_id:
        return

    quiz_data = user_quiz_state.get(user_id)

    # Проверяем, что викторина активна и это текущий вопрос
    if not quiz_data or quiz_data['current_index'] != question_index:
        return

    # Получаем выбранный ответ
    if 0 <= answer_index < len(quiz_data['current_answers']):
        selected_answer = quiz_data['current_answers'][answer_index]
    else:
        selected_answer = None

    correct_answer = quiz_data.get('correct_answer')

    # Проверяем ответ
    is_correct = selected_answer == correct_answer

    if is_correct:
        quiz_data['correct_answers'] += 1
        result_text = f"✅ <b>Правильно!</b>\n{quiz_data['words'][question_index]['word_eng']} = {correct_answer}"
    else:
        result_text = f"❌ <b>Неправильно!</b>\n{quiz_data['words'][question_index]['word_eng']} = {correct_answer}"

    # Отображаем результат, редактируя сообщение с вопросом
    bot.edit_message_text(
        result_text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='HTML'
    )

    # Увеличиваем счетчик вопроса
    quiz_data['current_index'] += 1

    # Ждем 0.5 секунды перед следующим вопросом
    threading.Timer(0.5, ask_quiz_question, args=[user_id]).start()


def finish_quiz(user_id):
    """Завершает викторину и показывает результаты"""
    quiz_data = user_quiz_state.pop(user_id, None)

    if not quiz_data:
        return

    correct = quiz_data['correct_answers']
    total = quiz_data['total_words']
    percentage = (correct / total) * 100 if total > 0 else 0

    # Сообщение о завершении викторины
    finish_message = f"<b>Вы повторили {total} слов!</b>\n\n"
    finish_message += f"Результат: {correct} из {total}\n\n"

    # Отправляем сообщение о завершении
    bot.send_message(quiz_data['chat_id'], finish_message, parse_mode='HTML')

    # Создаем и отправляем меню с кнопками
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Учим новые", callback_data="new_words")
    button_2 = telebot.types.InlineKeyboardButton("Повторяем старые", callback_data="repeat_words")
    button_3 = telebot.types.InlineKeyboardButton("Мои успехи", callback_data="user_stats")

    markup.add(button_1, button_2, button_3)

    bot.send_message(
        quiz_data['chat_id'],
        "Что дальше?",
        reply_markup=markup
    )



@bot.callback_query_handler(func=lambda call: call.data == "eng_rus")
def repeat_words_eng_rus(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id

    # Получаем слова для викторины
    words = get_five_random_words(user_id=user_id, learned=True)

    if not words:
        bot.send_message(call.message.chat.id, "У вас нет изученных слов для повторения!")
        return

    # Инициализируем состояние викторины для пользователя
    user_quiz_state[user_id] = {
        'words': words,
        'current_index': 0,
        'correct_answers': 0,
        'total_words': len(words),
        'chat_id': call.message.chat.id,
        'start_message_id': call.message.message_id  # Сохраняем ID начального сообщения
    }

    # Запускаем первый вопрос
    ask_quiz_question(user_id)


def ask_quiz_question(user_id):
    """Задает следующий вопрос викторины"""
    quiz_data = user_quiz_state.get(user_id)

    # Проверяем, есть ли активная викторина
    if not quiz_data:
        return

    # Проверяем, не завершена ли викторина
    if quiz_data['current_index'] >= quiz_data['total_words']:
        finish_quiz(user_id)
        return

    # Получаем текущее слово
    word_dict = quiz_data['words'][quiz_data['current_index']]

    # Генерируем варианты ответов
    ans_var = get_three_random_word()
    # Добавляем верный вариант ответа
    ans_var.append(word_dict.get("word_rus"))
    random.shuffle(ans_var)

    # Сохраняем правильный ответ для проверки
    quiz_data['correct_answer'] = word_dict.get("word_rus")
    quiz_data['current_answers'] = ans_var  # Сохраняем варианты для текущего вопроса

    # Создаем клавиатуру с уникальными callback_data
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    buttons = []

    # Генерируем callback_data по индексу в списке
    for i, answer in enumerate(ans_var):
        # Формат: quiz_userId_questionIndex_answerIndex
        callback_data = f"quiz_{user_id}_{quiz_data['current_index']}_{i}"
        button = telebot.types.InlineKeyboardButton(answer, callback_data=callback_data)
        buttons.append(button)

    markup.add(*buttons)

    # Отправляем вопрос (не удаляем предыдущие сообщения)
    message = bot.send_message(
        quiz_data['chat_id'],
        f"Вопрос {quiz_data['current_index'] + 1}/{quiz_data['total_words']}\n"
        f"Выберите правильный вариант. <b>{word_dict.get('word_eng')}</b> это:",
        reply_markup=markup,
        parse_mode='HTML'
    )

    # Сохраняем ID сообщения с вопросом
    quiz_data['last_question_message_id'] = message.message_id


@bot.callback_query_handler(func=lambda call: call.data.startswith("quiz_"))
def handle_quiz_answer(call):
    bot.answer_callback_query(call.id)

    # Парсим callback_data
    parts = call.data.split("_")
    if len(parts) < 4:
        return

    user_id = int(parts[1])
    question_index = int(parts[2])
    answer_index = int(parts[3])

    # Проверяем, что ответ от того же пользователя
    if call.from_user.id != user_id:
        return

    quiz_data = user_quiz_state.get(user_id)

    # Проверяем, что викторина активна и это текущий вопрос
    if not quiz_data or quiz_data['current_index'] != question_index:
        return

    # Получаем выбранный ответ
    if 0 <= answer_index < len(quiz_data['current_answers']):
        selected_answer = quiz_data['current_answers'][answer_index]
    else:
        selected_answer = None

    correct_answer = quiz_data.get('correct_answer')

    # Проверяем ответ
    is_correct = selected_answer == correct_answer

    if is_correct:
        quiz_data['correct_answers'] += 1
        result_text = f"✅ <b>Правильно!</b>\n{quiz_data['words'][question_index]['word_eng']} = {correct_answer}"
    else:
        result_text = f"❌ <b>Неправильно!</b>\n{quiz_data['words'][question_index]['word_eng']} = {correct_answer}"

    # Отображаем результат, редактируя сообщение с вопросом
    bot.edit_message_text(
        result_text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='HTML'
    )

    # Увеличиваем счетчик вопроса
    quiz_data['current_index'] += 1

    # Ждем 0.5 секунды перед следующим вопросом
    threading.Timer(0.5, ask_quiz_question, args=[user_id]).start()


def finish_quiz(user_id):
    """Завершает викторину и показывает результаты"""
    quiz_data = user_quiz_state.pop(user_id, None)

    if not quiz_data:
        return

    correct = quiz_data['correct_answers']
    total = quiz_data['total_words']
    percentage = (correct / total) * 100 if total > 0 else 0

    # Сообщение о завершении викторины
    finish_message = f"<b>Вы повторили {total} слов!</b>\n\n"
    finish_message += f"Результат: {correct} из {total}\n\n"

    # Отправляем сообщение о завершении
    bot.send_message(quiz_data['chat_id'], finish_message, parse_mode='HTML')

    # Создаем и отправляем меню с кнопками
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Учим новые", callback_data="new_words")
    button_2 = telebot.types.InlineKeyboardButton("Повторяем старые", callback_data="repeat_words")
    button_3 = telebot.types.InlineKeyboardButton("Мои успехи", callback_data="user_stats")

    markup.add(button_1, button_2, button_3)

    bot.send_message(
        quiz_data['chat_id'],
        "Что дальше?",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == "user_stats")
def user_stats(call):
    session = Session()
    bot.answer_callback_query(call.id)
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

    bot.send_message(call.message.chat.id,
                     f"<b>{user_name}</b>, ты знаешь уже {learned_words} слов! Всего слов: {unlearned_words + learned_words} Осталось выучить {unlearned_words}")

    session.close()

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Учим новые", callback_data="new_words")
    button_2 = telebot.types.InlineKeyboardButton("Повторяем старые", callback_data="repeat_words")
    button_3 = telebot.types.InlineKeyboardButton("Мои успехи", callback_data="user_stats")

    markup.add(button_1, button_2, button_3)

    bot.send_message(
        call.message.chat.id,
        "Что дальше?",
        reply_markup=markup
    )

if __name__ == "__main__":
    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=30
    )
