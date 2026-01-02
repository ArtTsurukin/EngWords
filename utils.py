from sqlalchemy import and_, func
from database import Session
from database.models import UserWordAssociation, Word


# Функция получает 5 англ слов с переводом
def get_five_random_words(user_id, learned=False):

    session = Session()

    # Собираем join из двух таблиц, limit на 5 записей, func.random(получаем случайные)
    try:
        unlearned_words = session.query(
            UserWordAssociation, Word
        ).join(
            Word, UserWordAssociation.word_id == Word.id
        ).filter(
            and_(
                UserWordAssociation.user_id == user_id,
                UserWordAssociation.learned == learned
            )
        ).order_by(
            func.random()
        ).limit(5).all()

        if not unlearned_words:
            return []

        # Подготавливаем данные для возврата
        words_data = []
        for association, word in unlearned_words:
            # Добавляем информацию о слове
            words_data.append({
                'word_eng': word.word_eng,
                'word_rus': word.word_rus,
                'word_id': word.id,
                'association_id': (association.user_id, association.word_id)
            })
        # Помечаем эти слова как изученные (learned = True)
        # Получаем ID слов для обновления
        if not learned:
            word_ids_to_update = [word.id for _, word in unlearned_words]
            # Обновляем статус в базе данных
            session.query(UserWordAssociation).filter(
                and_(
                    UserWordAssociation.user_id == user_id,
                    UserWordAssociation.word_id.in_(word_ids_to_update)
                )
            ).update(
                {UserWordAssociation.learned: True},
                synchronize_session=False
            )

        session.commit()
        return words_data

    except Exception as e:
        session.rollback()
        print(f"Error in get_ten_random_words: {e}")
        return []

    finally:
        session.close()


# Создаем словарь с тремя неверными вариантами ответа
def get_three_random_word(rus_or_eng: str):
    session = Session()
    word_data = session.query(Word).order_by(func.random()).limit(3).all()
    three_word = []
    session.close()
    for word in word_data:
        three_word.append(word.rus_or_eng)
    return three_word


