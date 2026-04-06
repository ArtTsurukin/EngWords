import random

import telebot.types
from utils import get_three_random_word

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




async def send_next_word(bot,
                         chat_id,
                         user_id,
                         user_repeat_state,
                         message=None,
                         message_id=None
                         ):
    # Отправляем следующее слово пользователю
    # Удаляем предыдущее сообщение с вопросом(очищаем диалог)
    # if message:
    #     message_id_for_delete = message.message_id - 1
    #     await bot.delete_message(message.chat.id, message_id_for_delete)
    state = user_repeat_state.get(user_id)
    mode = state.get("mode")
    mode_lang = state.get("mode_lang")
    if not state or state['current_index'] >= len(state['words']):
        # Викторина завершена
        text = "Проверка окончена"
        if message_id:
            await bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=text
            )

        # Если цикл завершен очищаем запись в словаре по user_id, выходим в главное меню
        if user_id in user_repeat_state:
            del user_repeat_state[user_id]
        await main_menu(bot=bot, chat_id=chat_id)
        return

    current_word = state["words"][state["current_index"]]
    word_rus = current_word.get('word_rus')
    word_eng = current_word.get('word_eng')

    # Сохраняем правильный ответ в состоянии
    state['current_answer'] = word_eng

    # Отправляем слово на русском
    text = f"Введите перевод на английском: <b>{word_rus}</b>"

    if mode_lang == "eng_rus":
        state['current_answer'] = word_rus
        text = f"Введите перевод на русском: <b>{word_eng}</b>"

    key_for_answer = "word_eng" if mode_lang == "rus_eng" else "word_rus"
    markup = None

    # Создаем клавиатуру с ответами если режим button
    if mode == "button":

        answers_list = get_three_random_word(lang_word=key_for_answer)
        answers_list.append(state.get("current_answer"))
        random.shuffle(answers_list)

        markup = telebot.types.InlineKeyboardMarkup(row_width=2)

        button_1 = telebot.types.InlineKeyboardButton(answers_list[0], callback_data=f"ans_but:{answers_list[0]}")
        button_2 = telebot.types.InlineKeyboardButton(answers_list[1], callback_data=f"ans_but:{answers_list[1]}")
        button_3 = telebot.types.InlineKeyboardButton(answers_list[2], callback_data=f"ans_but:{answers_list[2]}")
        button_4 = telebot.types.InlineKeyboardButton(answers_list[3], callback_data=f"ans_but:{answers_list[3]}")

        markup.add(button_1, button_2, button_3, button_4)


    if message_id:
        await bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup
            )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=markup
            )


async def send_next_word_button():
    pass