import sqlite3


class Chat_data_class:
    def __init__(self):
        with sqlite3.connect('chat.db') as connect:
            cursor = connect.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS chat(
            Chat_ID INTEGER,
            Title TEXT,
            Link TEXT,
            Count INTEGER,
            Admin_ID INTEGER)''')


    def add_chat(self, chat_id, title, link, count, admin_id):
        with sqlite3.connect('chat.db') as connect:
            cursor = connect.cursor()
            cursor.execute('''SELECT Chat_ID FROM chat WHERE Chat_ID = ?''', (chat_id,))
            checker = cursor.fetchone()
            if not checker:
                cursor.execute('''INSERT INTO chat VALUES(?,?,?,?,?)''', (chat_id, title, link, count, admin_id))


    def del_chat(self, chat_id, admin_id):
        with sqlite3.connect('chat.db') as connect:
            cursor = connect.cursor()
            cursor.execute('''DELETE FROM chat WHERE Chat_ID = ? AND Admin_ID = ?''', (chat_id, admin_id))

    def get_all_chat_id(self):
        with sqlite3.connect('chat.db') as connect:
            cursor = connect.cursor()
            cursor.execute('''SELECT Chat_ID FROM chat''')
            data = cursor.fetchall()
            result = []
            for chat_id in data:
                result.append(chat_id[0])
            return result

    def get_chat_data(self):
        with sqlite3.connect('chat.db') as connect:
            cursor = connect.cursor()
            cursor.execute('''SELECT Chat_ID, Title, Link, Count FROM chat''')
            data = cursor.fetchall()
            return data

    def get_user_chat(self, user_id):
        with sqlite3.connect('chat.db') as connect:
            cursor = connect.cursor()
            cursor.execute('''SELECT Chat_ID, Title, Link FROM chat WHERE Admin_ID = ?''', (user_id,))
            data = cursor.fetchall()
            return data