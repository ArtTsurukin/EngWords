from sqlalchemy import and_, func
from database import Session
from database.models import UserWordAssociation, Word
from menus import main_menu

import tracemalloc
import telebot.types
import random


tracemalloc.start()
# Функция получает заданное количество англ слов с переводом
def get_any_random_words(howmuch: int,
                         user_id: int,
                         learning_status_for_request: str):

    session = Session()

    # Собираем join из двух таблиц, limit на howmuch записей, func.random(получаем случайные)
    try:
        ten_words = session.query(
            UserWordAssociation, Word
        ).join(
            Word, UserWordAssociation.word_id == Word.id
        ).filter(
            and_(
                UserWordAssociation.user_id == user_id,
                UserWordAssociation.learning_status == learning_status_for_request
            )
        ).order_by(
            func.random()
        ).limit(howmuch).all()

        if not ten_words:
            return []

        # Подготавливаем данные для возврата
        words_data = []
        for association, word in ten_words:
            # Добавляем информацию о слове
            words_data.append({
                'word_eng': word.word_eng,
                'word_rus': word.word_rus,
                'word_id': word.id,
                'association_id': (association.user_id, association.word_id)
            })

        session.commit()
        return words_data

    except Exception as e:
        session.rollback()
        print(f"Error in get_ten_random_words: {e}")
        return []

    finally:
        session.close()


# Создаем словарь с тремя неверными вариантами ответа
def get_three_random_word(lang_word: str):
    session = Session()
    word_data = session.query(Word).order_by(func.random()).limit(3).all()
    three_word = []
    session.close()
    for word in word_data:
        x = getattr(word, lang_word)
        three_word.append(x)
    return three_word


def set_learning_status(word_for_learn: dict,
                        user_id: int,
                        set_status: str):
    session = Session()

    try:
        word_id = word_for_learn[0].get("word_id")

        # Находим ассоциацию по user_id и word_id
        association = session.query(UserWordAssociation).filter_by(
            user_id=user_id,
            word_id=word_id
        ).first()

        if association:
            # Меняем статус на "learned"
            association.learning_status = set_status
            session.commit()
            return True
        else:
            session.rollback()
            return False

    except Exception as e:
        session.rollback()
        print(f"Ошибка при обновлении статуса: {e}")
        raise
    finally:
        session.close()




async def send_next_word_for_learn(bot, chat_id, message_id, user_id, user_learn_state):
    state = user_learn_state[user_id]

    if not state or len(state["words"]) > 10:
        # Набор новых слов для изучения закончен
        text = "10 новых слов для изучения набраны"
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
        if user_id in user_learn_state:
            del user_learn_state[user_id]
        await main_menu(bot=bot, chat_id=chat_id)
        return

    words = user_learn_state[user_id].get("words")
    word_eng = words[-1].get("word_eng")
    word_rus = words[-1].get("word_rus")

    text = f"Знаете это слово? <b>{word_eng}</b> ответ: <tg-spoiler><b>{word_rus}</b></tg-spoiler>"

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_1 = telebot.types.InlineKeyboardButton("Знаю", callback_data="already_known")
    button_2 = telebot.types.InlineKeyboardButton("Не знаю", callback_data="will_learn")
    button_3 = telebot.types.InlineKeyboardButton("Главное меню", callback_data="back:show_main_menu")

    markup.add(button_1, button_2, button_3)


    await bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


#send_next_word_button(user_id=837000924)


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