import sqlite3, os, random, messages
from telebot import TeleBot, types, formatting
from config import telegram_channel_link, BOT_TOKEN

bot = TeleBot(BOT_TOKEN)

conn = sqlite3.connect('avtos.db', check_same_thread=False)
cursor = conn.cursor()

def initialize_db():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS avto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            feedback_text TEXT,
            reting INTEGER
        );
    ''')
    conn.commit()

initialize_db()


latest_works = {
    'Рули': ['761.jpg', '718.jpg'], 
    'Салоны': [],
    'Потолки': [],
    'Вышивки': []
}

feedbacks = []

IMAGE_DIR = 'images'
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

@bot.message_handler(commands=['start'])
def start_message(message):
    sticker_id = 'CAACAgIAAxkBAAKWuGdI4Fe4nvFJOuucwXHQsbuoS9Q1AAI1AQACMNSdEbS4Nf1moLZ8NgQ'
    bot.send_sticker(message.chat.id, sticker_id)
    response = random.choice(messages.start_message)
    markup = create_start_markup()
    bot.send_message(message.chat.id, response, reply_markup=markup)

def create_start_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_job = types.KeyboardButton('🔎 Последние Работы')
    btn_info = types.KeyboardButton('ℹ️ Информация')
    btn_feedback = types.KeyboardButton('⭐️ Отзыв')
    btn_rewars = types.KeyboardButton('📣 Все отзывы')
    btn_map = types.KeyboardButton("🗺 Где мы находимся")
    markup.add(btn_job, btn_rewars)
    markup.add(btn_feedback, btn_info)
    markup.add(btn_map)
    return markup

@bot.message_handler(func=lambda message: message.text == '🔎 Последние Работы')
def last_category_work(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_rul = types.KeyboardButton('Рули')
    btn_salon = types.KeyboardButton('Салоны')
    btn_potolok = types.KeyboardButton('Потолки')
    markup.add(btn_rul, btn_salon)
    markup.add(btn_potolok)
    markup.add(types.KeyboardButton('⬅️ Назад'))
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)

def send_photos_from_category(chat_id, category):
    for photo_path in latest_works[category]:
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo:
                bot.send_photo(chat_id, photo)

@bot.message_handler(func=lambda message: message.text == '🗺 Где мы находимся')
def message_map(message):
    latitude = 46.358748
    longitude = 48.092962
    bot.send_location(message.chat.id, latitude=latitude, longitude=longitude)
    bot.send_message(message.chat.id, 'Мы находимся по указанному адрессу')

@bot.message_handler(func=lambda message: message.text == 'ℹ️ Информация')
def information_message(message):
    bot.send_message(message.chat.id, messages.info_message)

@bot.message_handler(func=lambda message: message.text == '⬅️ Назад')
def back_to_previous(message):

    bot.send_message(message.chat.id, "Вы вернулись назад. Выберите другое действие.")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_job = types.KeyboardButton('🔎 Последние Работы')
    btn_info = types.KeyboardButton('ℹ️ Информация')
    btn_feedback = types.KeyboardButton('⭐️ Отзыв')
    btn_map = types.KeyboardButton("🗺 Где мы находимся")
    btn_rewars = types.KeyboardButton('📣 Все отзывы')
    markup.add(btn_job, btn_rewars)
    markup.add(btn_feedback, btn_info)
    markup.add(btn_map)
    
    bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '⭐️ Отзыв')
def handle_username(message):
    bot.send_message(message.chat.id, "Пожалуйста, введите ваше имя:")
    bot.register_next_step_handler(message, handle_add_feedback)

def handle_add_feedback(message):
    username = message.text
    bot.send_message(message.chat.id, "Пожалуйста, введите ваш отзыв:")
    bot.register_next_step_handler(message, lambda msg: request_rating(msg, username))

def request_rating(message, username):
    feedback_text = message.text
    bot.send_message(message.chat.id, "Пожалуйста, введите вашу оценку (от 1 до 5):")
    bot.register_next_step_handler(message, lambda msg: save_feedback(msg, username, feedback_text))

def save_feedback(message, username, feedback_text):
    try:
        rating = int(message.text)
        if 1 <= rating <= 5:
            cursor.execute('INSERT INTO avto (username, feedback_text, reting) VALUES (?, ?, ?)', 
                           (username, feedback_text, rating))
            conn.commit()

            stars = '⭐️' * rating
            text = f"Оценка работы: {stars},\n➖➖➖➖➖➖\n{username}: {feedback_text}\n"
            bot.send_message(message.chat.id, "Ваш отзыв сохранен!")
        else:
            bot.send_message(message.chat.id, "Некорректная оценка. Пожалуйста, введите число от 1 до 5.")
            bot.register_next_step_handler(message, lambda msg: save_feedback(msg, username, feedback_text))
    except ValueError:
        bot.send_message(message.chat.id, "Это не число. Пожалуйста, введите число от 1 до 5.")
        bot.register_next_step_handler(message, lambda msg: save_feedback(msg, username, feedback_text))

@bot.message_handler(func=lambda message: message.text == '📣 Все отзывы')
def handle_rewards(message):
    cursor.execute('SELECT username, feedback_text, reting FROM avto')
    feedbacks = cursor.fetchall()
    
    if feedbacks:
        all_feedbacks = '\n'.join([f"Оценка: {'⭐️' * rating}\n➖➖➖➖➖➖\n{username}: {feedback_text}\n" for username, feedback_text, rating in feedbacks])
        bot.send_message(message.chat.id, "Вот все отзывы:\n" + all_feedbacks)
    else:
        bot.send_message(message.chat.id, 'Нет отзывов')

@bot.message_handler(func=lambda message: message.text in latest_works.keys())
def works_message(message):
    category = message.text
    
    if category not in latest_works:
        bot.send_message(message.chat.id, "Категория не найдена.")
        return

    works_response = "\n" if latest_works[category] else "Нет работ в категории."

    media = []
    for photo_filename in latest_works[category]:
        photo_path = os.path.join(IMAGE_DIR, photo_filename) 
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo_file:
                media.append(types.InputMediaPhoto(photo_file.read(), caption=works_response if not media else None))

    if media:
        bot.send_media_group(message.chat.id, media)
        bot.send_message(message.chat.id, f"Вот все работы категории " + category + "\nПодписывайтесь на наш канал: " + telegram_channel_link)
    else:
        bot.send_message(message.chat.id, 'В данной категории нету работ')

if __name__ == '__main__':
    bot.polling(none_stop=True)
