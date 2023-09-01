import aiogram
from aiogram.types import Message, CallbackQuery
from aiogram import Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageToPinNotFound

import pyrogram
from pyrogram.errors.exceptions.bad_request_400 import UserAlreadyParticipant
from pyrogram.enums.chat_type import ChatType

from database.user import User_data_class
from database.chat import Chat_data_class
from keyboard import client_keyboard
import config

User_data = User_data_class()
Chat_data = Chat_data_class()
client_pyrogram = pyrogram.Client("my_account", config.API_ID, config.API_HASH)
client_pyrogram.start()


class FSM_ADD_CHAT(StatesGroup):
    link = State()

async def pin_msg(message: Message):
    try:
        if message.sender_chat.type == 'channel':
            await message.unpin()
    except:
        pass


async def start(message: Message):
    '''Пользователь нажал старт'''
    user_id = message.from_user.id
    name = message.from_user.first_name
    surname = message.from_user.last_name

    username = message.from_user.username

    User_data.add_user(user_id, name, username, surname)
    await message.answer(f'Привет, {name}.\n\n', reply_markup=client_keyboard.main_menu())


async def add_chat(message: Message, state: FSMContext):
    '''Пользователь нажал добавить чат'''
    await state.finish()
    await message.answer('Добавь меня в администраторы чата, дай ему право закреплять сообщение и пришли ссылку')
    await FSM_ADD_CHAT.link.set()

async def add_chat2(message: Message, state: FSMContext):
    if ('joinchat' in message.text) or ('+' in message.text):
        try:
            await client_pyrogram.join_chat(message.text)  # присоединение к чату

        except UserAlreadyParticipant:
            pass
        chat = await client_pyrogram.get_chat(message.text)
        chat_id = chat.id
        await client_pyrogram.leave_chat(chat_id)  # ливаем из чата
        if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
            await message.answer('Ссылка должна быть на группу')
            await state.finish()
            return

        try:#Проверяем добавили ли бота в админы и дали ли ему право закреплять сообщения
            await message.bot.pin_chat_message(chat_id, 9999999999999)
        except MessageToPinNotFound:#если добавили то срабуоте исключение
            Chat_data.add_chat(chat_id, chat.title, message.text, chat.members_count, message.from_user.id)
            await message.answer(f'Чат {chat.title} добавлен')
            await state.finish()
        else:
            await message.answer('Похоже что ты не добавил бота в администраторы или не дал ему право закреплять сообщения')
            await state.finish()


    else:
        link = message.text
        if '/' in message.text:
            link = message.text.split('/')[-1]
        chat = await client_pyrogram.get_chat(link)
        if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
            await message.answer('Ссылка должна быть на группу')
            await state.finish()
            return

        chat_id = chat.id
        try: #Проверяем добавили ли бота в админы и дали ли ему право закреплять сообщения
            await message.bot.pin_chat_message(chat_id, 9999999999999)
        except MessageToPinNotFound:#если добавили то срабуоте исключение
            Chat_data.add_chat(chat_id, chat.title, message.text, chat.members_count, message.from_user.id)
            await message.answer(f'Чат {chat.title} добавлен')
            await state.finish()
        except:
            await message.answer('Похоже что ты не добавил бота в администраторы или не дал ему право закреплять сообщения')



async def get_my_chat(message: Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    chat_data = Chat_data.get_user_chat(user_id)
    if len(chat_data) < 1:
        await message.answer('Ты не добавил еще чатов')
        return
    text = '<b>Твои чаты</b>\n\n'
    for chat_id, title, link in chat_data:
        text+=f'{title} - {link}\n'
    await message.answer(text, parse_mode='HTML')


async def del_chat(message: Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    chat_data = Chat_data.get_user_chat(user_id)
    if len(chat_data) < 1:
        await message.answer('Ты не добавил еще чатов')
        return
    text = '<b>Выбери чат который хочешь удалить</b>\n\n'
    for chat_id, title, link in chat_data:
        text+=f'{title} - {link}\n'
    await message.answer(text, reply_markup=client_keyboard.del_chat(chat_data), parse_mode='HTML', disable_web_page_preview=True)

async def del_chat2(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await call.answer()
    chat_id = int(call.data.split('_')[-1])
    await call.message.answer('Ты уверен что хочешь удалить бота из чата?', reply_markup=client_keyboard.conf_del_chat(chat_id))

async def del_chat3(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await call.answer()
    chat_id = int(call.data.split('_')[-1])
    user_id = call.from_user.id
    Chat_data.del_chat(chat_id, user_id)
    await call.message.answer('Чат удален')

async def no_del(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await call.answer()
    user_id = call.from_user.id
    await call.bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
    await call.message.answer(f'Привет, {call.from_user.first_name}.\n\n', reply_markup=client_keyboard.main_menu())

def register_client(dp: Dispatcher):
    dp.register_message_handler(start, lambda message: message.from_user.id == message.chat.id, commands='start', state='*')
    dp.register_message_handler(add_chat, lambda message: (message.text=='Добавить чат') and (message.from_user.id == message.chat.id) , state='*')
    dp.register_message_handler(add_chat2, state=FSM_ADD_CHAT.link)
    dp.register_message_handler(get_my_chat, lambda message: (message.text=='Получить свои чаты') and ( message.from_user.id == message.chat.id), state='*')
    dp.register_message_handler(del_chat, lambda message: (message.text=='Удалить чат') and ( message.from_user.id == message.chat.id), state='*')
    dp.register_callback_query_handler(del_chat2, lambda call: call.data.startswith('del_'), state='*')
    dp.register_callback_query_handler(del_chat3, lambda call: call.data.startswith('dell_'), state='*')
    dp.register_callback_query_handler(no_del, lambda call: call.data=='nodel', state='*')

    dp.register_message_handler(pin_msg, lambda message: message.chat.id in Chat_data.get_all_chat_id(), content_types=['any'])