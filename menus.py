import telebot.types


async def main_menu(bot, chat_id, message_id=None):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Учим новые", callback_data="new_words")
    button_2 = telebot.types.InlineKeyboardButton("Повторяем старые", callback_data="repeat_words")
    button_3 = telebot.types.InlineKeyboardButton("Мои успехи", callback_data="user_stats")

    markup.add(button_1, button_2, button_3)

    text = "Нажмите кнопку:"

    if message_id:
        await bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
    else:
        await bot.send_message(chat_id, text, reply_markup=markup)


async def select_mode_lang_write(bot, chat_id, message_id):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("RU-ENG", callback_data="rus_eng_write")
    button_2 = telebot.types.InlineKeyboardButton("ENG-RU", callback_data="eng_rus_write")
    button_3 = telebot.types.InlineKeyboardButton("Назад", callback_data="back:select_mode")

    markup.add(button_1, button_2, button_3)

    text = "Выберите режим:"

    await bot.edit_message_text(
        text,
        chat_id,
        message_id,
        reply_markup=markup
    )

async def select_mode_lang_button(bot, chat_id, message_id):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("RU-ENG", callback_data="rus_eng_button")
    button_2 = telebot.types.InlineKeyboardButton("ENG-RU", callback_data="eng_rus_button")
    button_3 = telebot.types.InlineKeyboardButton("Назад", callback_data="back:select_mode")

    markup.add(button_1, button_2, button_3)

    text = "Выберите режим"

    await bot.edit_message_text(
        text,
        chat_id,
        message_id,
        reply_markup=markup
    )



async def select_mode(bot, chat_id, message_id):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Ввод вручную", callback_data="write_mode")
    button_2 = telebot.types.InlineKeyboardButton("Ввод кнопками", callback_data="button_mode")
    button_3 = telebot.types.InlineKeyboardButton("Главное меню", callback_data="back:show_main_menu")

    markup.add(button_1, button_2, button_3)
    text = "Нажмите:"
    await bot.edit_message_text(
        text,
        chat_id,
        message_id,
        reply_markup=markup
    )




