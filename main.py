from datetime import datetime
import os
import sqlite3
import threading
import random
import telebot
import openai
import time
import configparser

config = configparser.ConfigParser()  # создаём объекта парсера
config.read("settings.ini")  # читаем конфиг
'''
[settings]
token_chatgtp = *******
chat_id = *******
token_telegram = *******
message_id = *******
'''


start_time = time.time()
chat_id = (config["settings"]["chat_id"])
token_telegram = (config["settings"]["token_telegram"])
bot = telebot.TeleBot(token_telegram)
token_chatgtp = (config["settings"]["token_chatgtp"]).split(",")


def db_insert(texts, reply, lens):
    con = sqlite3.connect("metanit.db")
    cursor = con.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS base(
       userid INT PRIMARY KEY,
       texts TEXT,
       reply TEXT,
       lens TEXT);
    """)
    con.commit()

    cursor.execute("INSERT INTO base (texts, reply, lens)  VALUES (?, ?, ?)", (texts, reply, lens))
    con.commit()


def openais(token, text):
    messages = []
    openai.api_key = token
    messages.append({"role": "user", "content": text})
    chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    reply = chat.choices[0].message.content
    return reply


def sequential(calc, thead, count, token, text, from_use_id):
    for i in range(calc):
        print(f"Токен - {count}  Запускаем поток № {thead}  Цикл {i}")
        start_time = time.time()

        try:
            reply = openais(token, text)
            print(f'Время обработки: {int(time.time() - start_time)}\nКонтент:\n{reply}\n\n')
        except:
            print(f"Не обработан запрос для токена {token}")
            time.sleep(random.randint(5, 20))
            reply = openais(token, text)
            print(f'Время обработки: {int(time.time() - start_time)}\nКонтент:\n{reply}\n\n')
        print(len(reply))
        db_insert(text, reply, len(reply))  # запись в базу

        with open(f"{from_use_id}.txt", "a") as file:
            file.write(f'{reply}\n\n')
        # bot.send_message(chat_id=chat_id, text=reply)  # отправка боту x[3] - info


def threaded(theads, calc, tokens, text, info, from_use_id):
    threads = []
    # запуск потоков
    for thead in range(theads):
        for count, token in enumerate(tokens):
            t = threading.Thread(target=sequential, args=(calc, thead, count, token, text, from_use_id))
            threads.append(t)
            t.start()

    # Подождем, пока все потоки завершат свою работу.
    for t in threads:
        t.join()
        print(f'Поток {t} завершен')

    with open(f"{from_use_id}.txt", "r") as file:
        bot.send_document(chat_id, file)

    text = (f'Все потоки завершены\nВремя выполнения - {((time.time() - start_time))} сек')
    print(text)
    print("\n\n\n\n\n\n\n")
    bot.send_message(chat_id=chat_id, text=text)  # отправка боту x[3] - info


def math(colichestvo, text, token_chatgtp):
    # токен
    tokens = token_chatgtp
    if colichestvo <= 3:  # если запросов меньше 3
        theads = 1
        calc = 1
    else:
        theads = int((colichestvo / int(len(tokens))) ** 0.5)  # потоков
        calc = (int(colichestvo / int(len(tokens)) / theads))  # циклов

        # елси потоков больше 10 то не спрвиться chatgtp, ограничение так как
        if theads > 10:
            theads = 10  # потоков
            calc = (int(colichestvo / int(len(tokens)) / theads))  # циклов

    # инфа
    info = (f'Начало\n'
            f'Запросов: {colichestvo}\n'
            f'Токенов: {len(tokens)}\n'
            f'Потоков: {theads}\n'
            f'Циклов: {calc}\n'
            f'Текст: {text}')

    return theads, calc, tokens, info


def main(text, from_use_id):
    with open(f"{from_use_id}.txt", "w") as file:
        file.write('')
    # Входные данные
    # text = str(input("Введите вопрос: "))
    # colichestvo = int(input("Введите количество запросов: ") or "1")
    colichestvo = 1

    x = math(colichestvo, text, token_chatgtp)  # вычилсение количетсва запросов

    bot.send_message(chat_id=chat_id, text=x[3])  # отправка боту x[3] - info
    info = x[3]
    threaded(x[0], x[1], x[2], text, info,
             from_use_id)  # запуск основного кода theads = x[0], calc = x[1], tokens = x[2]


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
                 'Привет!\nЯ ChatGPT Telegram Bot\U0001F916\nЗадай мне любой вопрос и я постараюсь на него ответиь')


@bot.message_handler(func=lambda _: True)
def handle_message(message):
    text = message.text
    print(text)
    from_use_id = message.from_user.id
    print(from_use_id)
    main(text, from_use_id)


def theard_desktop():
    print('Введите запрос: ')
    while True:
        try:
            text = input()
            from_use_id = 'desktop'
            main(text, from_use_id)
        except:
            time.sleep(5)
            print(f"Проблема с соединением theard_desktop - {datetime.now()}")
            continue


def theard_tele():
    while True:
        try:
            bot.polling()
        except:
            time.sleep(5)
            print(f"Проблема с соединением theard_tele - {datetime.now()}")
            continue


def start():
    try:
        print('ChatGPT Bot is working')
        threading_telebot = threading.Thread(target=theard_tele)
        threading_telebot.start()
        threading_desktop = threading.Thread(target=theard_desktop)
        threading_desktop.start()
    except:
        print("Error start")
        time.sleep(5)
        start()


if __name__ in "__main__":
    start()
