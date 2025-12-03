import telebot.types
import config
import time

from telebot import TeleBot
from database import Session
from database.models import User, Word, UserWordAssociation
from sqlalchemy import and_
from utils import get_five_random_words, get_three_random_word, shuffle_dict

bot = TeleBot(token=config.BOT_TOKEN, parse_mode="HTML")


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
    bot.send_message(call.message.chat.id, "Вот новые слова:")
    for word_dict in words:
        bot.send_message(call.message.chat.id, f"<b>{word_dict.get('word_eng')}</b> - <i>{word_dict.get('word_rus')}</i>")
        time.sleep(1)


@bot.callback_query_handler(func=lambda call: call.data == "repeat_words")
def repeat_words(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    words = get_five_random_words(user_id=user_id, learned=True)
    for word_dict in words:

        # Получаем три неверных варианта для рендера ответов
        ans_var = get_three_random_word()
        # Добавляем один верный вариант
        ans_var[word_dict.get("word_rus")] = True
        # Перемешиваем словарь для случайного вывода ответов
        ans_var_shuf = shuffle_dict(d = ans_var)


        markup = telebot.types.InlineKeyboardMarkup(row_width=2)

        button_1 = telebot.types.InlineKeyboardButton(list(ans_var_shuf.keys())[0], callback_data=list(ans_var_shuf.keys())[0])
        button_2 = telebot.types.InlineKeyboardButton(list(ans_var_shuf.keys())[1], callback_data=list(ans_var_shuf.keys())[1])
        button_3 = telebot.types.InlineKeyboardButton(list(ans_var_shuf.keys())[2], callback_data=list(ans_var_shuf.keys())[2])
        button_4 = telebot.types.InlineKeyboardButton(list(ans_var_shuf.keys())[3], callback_data=list(ans_var_shuf.keys())[3])

        markup.add(button_1, button_2, button_3, button_4)

        bot.send_message(call.message.chat.id,
                         f"Выберете правильный вариант. <b><pre>{word_dict.get('word_eng')}</pre></b> это:",
                         reply_markup=markup, parse_mode='HTML')

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
                     f"<b>{user_name}</b>, ты знаешь уже {learned_words} слов! Осталось выучить {unlearned_words}")



if __name__ == "__main__":
    bot.infinity_polling()

