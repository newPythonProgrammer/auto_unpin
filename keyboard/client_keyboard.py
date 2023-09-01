from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    menu = ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = KeyboardButton(text='Добавить чат')
    btn2 = KeyboardButton(text='Получить свои чаты')
    btn3 = KeyboardButton(text='Удалить чат')
    menu.add(btn1, btn3)
    menu.add(btn2)
    return menu

def del_chat(data):
    menu = InlineKeyboardMarkup(row_width=1)
    for chat_id, title, link in data:
        menu.add(InlineKeyboardButton(text=f'{title}', callback_data=f'del_{chat_id}'))
    return menu

def conf_del_chat(chat_id):
    menu = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton(text='Да✅', callback_data=f'dell_{chat_id}')
    btn2 = InlineKeyboardButton(text='Нет❌', callback_data=f'nodel')
    menu.add(btn1, btn2)
    return menu