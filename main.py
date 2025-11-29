import telebot.types
from telebot import TeleBot

import config

bot = TeleBot(token=config.BOT_TOKEN, parse_mode=None)

@bot.message_handler(commands=["start"])
def send_start_message(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Учим новые", callback_data="new_words")
    button_2 = telebot.types.InlineKeyboardButton("Повторяем старые", callback_data="repeat_old")

    markup.add(button_1, button_2)

    bot.send_message(message.chat.id, f"Привет {message.from_user.first_name}, нажмите кнопку:", reply_markup=markup)


@bot.message_handler(content_types=["text"])
def send_echo(message):
    bot.send_message(message.chat.id, f"You send me {message.text}")

if __name__ == "__main__":
    bot.infinity_polling()

