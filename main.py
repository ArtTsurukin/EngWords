import telebot.types
import config

from telebot import TeleBot
from database import Session
from database.models import User, Word, UserWordAssociation
from sqlalchemy import and_, or_

bot = TeleBot(token=config.BOT_TOKEN, parse_mode=None)


@bot.message_handler(commands=["start"])
def send_start_message(message):
    user_id = message.from_user.id
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


    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Учим новые", callback_data="new_words")
    button_2 = telebot.types.InlineKeyboardButton("Повторяем старые", callback_data="repeat_old")
    button_3 = telebot.types.InlineKeyboardButton("Мои успехи", callback_data="user_stats")

    markup.add(button_1, button_2, button_3)

    bot.send_message(message.chat.id, f"Привет {message.from_user.first_name}, нажмите кнопку:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "new_words")
def new_words(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "New words!")



@bot.callback_query_handler(func=lambda call: call.data == "repeat_old")
def new_words(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Repeat old words!")



@bot.callback_query_handler(func=lambda call: call.data == "user_stats")
def handle_my_profile(call):
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
            UserWordAssociation.learned == True
        )
    ).count()

    bot.send_message(call.message.chat.id,
                     f"{user_name}, ты знаешь уже {learned_words} слов! Осталось выучить {unlearned_words}")



if __name__ == "__main__":
    bot.infinity_polling()

