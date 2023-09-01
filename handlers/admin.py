from aiogram import Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, MediaGroup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types

import ast
import asyncio
from typing import List, Union

import config
from database.spam import Spam_data_class
from database.user import User_data_class
from database.chat import Chat_data_class

User_data = User_data_class()
Spam_data = Spam_data_class()
Chat_data = Chat_data_class()


class FSM_ADMIN_SPAM(StatesGroup):
    text = State()
    btns = State()

class AlbumMiddleware(BaseMiddleware):
    """This middleware is for capturing media groups."""

    album_data: dict = {}

    def __init__(self, latency: Union[int, float] = 0.01):
        """
        You can provide custom latency to make sure
        albums are handled properly in highload.
        """
        self.latency = latency
        super().__init__()

    async def on_process_message(self, message: Message, data: dict):
        if not message.media_group_id:
            return

        try:
            self.album_data[message.media_group_id].append(message)
            raise CancelHandler()  # Tell aiogram to cancel handler for this group element
        except KeyError:
            self.album_data[message.media_group_id] = [message]
            await asyncio.sleep(self.latency)

            message.conf["is_last"] = True
            data["album"] = self.album_data[message.media_group_id]

    async def on_post_process_message(self, message: Message, result: dict, data: dict):
        """Clean up after handling our album."""
        if message.media_group_id and message.conf.get("is_last"):
            del self.album_data[message.media_group_id]


async def stat(message: Message):
    user_id = message.from_user.id
    if user_id in config.ADMINS:
        await message.answer(User_data.get_stat())
        chat_data = Chat_data.get_chat_data()
        count_chat = 0
        count_member = 0
        text = '<b>Название|Ссылка|Участников</b>\n\n'
        for chat_id, title, link, count in chat_data:
            text+=f'{title}|{link} |{count}\n'
            count_chat+=1
            count_member+=count
        await message.answer(f'{text}\n'
                             f'Всего: {count_chat} чатов и {count_member} участников', parse_mode='HTML')


async def spam1(message: Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    if user_id in config.ADMINS:
        await message.answer('Пришли пост')
        await FSM_ADMIN_SPAM.text.set()


async def spam2_media_group(message: Message, album: List[Message], state: FSMContext):
    """This handler will receive a complete album of any type."""
    media_group = MediaGroup()
    for obj in album:
        if obj.photo:
            file_id = obj.photo[-1].file_id
        else:
            file_id = obj[obj.content_type].file_id

        try:
            # We can also add a caption to each file by specifying `"caption": "text"`
            media_group.attach({"media": file_id, "type": obj.content_type, "caption": obj.caption,
                                "caption_entities": obj.caption_entities})
        except ValueError:
            return await message.answer("This type of album is not supported by aiogram.")
    media_group = ast.literal_eval(str(media_group))
    async with state.proxy() as data:
        try:
            data['text'] = media_group[0]['caption']
        except:
            data['text'] = 'None'
        data['media'] = media_group
        Spam_data.make_spam(data['text'], 'None', str(media_group))

    await message.answer_media_group(media_group)
    await message.answer(f'Пришли команду /sendspam_{Spam_data.select_id()} чтоб начать рассылку')
    await state.finish()


async def spam2(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in config.ADMINS:
        if message.content_type in ('photo', 'video', 'animation'):
            async with state.proxy() as data:
                try:
                    data['text'] = message.html_text
                except:
                    data['text'] = None
                if message.content_type == 'photo':
                    data['media'] = ('photo', message.photo[-1].file_id)
                else:
                    data['media'] = (message.content_type, message[message.content_type].file_id)
        else:
            async with state.proxy() as data:
                data['text'] = message.html_text
                data['media'] = 'None'
        await message.answer('Теперь пришли кнопки например\n'
                             'text - url1\n'
                             'text2 - url2 && text3 - url3\n\n'
                             'text - надпись кнопки url - ссылка'
                             '"-" - разделитель\n'
                             '"&&" - склеить в строку\n'
                             'ЕСЛИ НЕ НУЖНЫ КНОПКИ ОТПРАВЬ 0')
        await FSM_ADMIN_SPAM.next()


async def spam3(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in config.ADMINS:
        if message.text != '0':
            # конструктор кнопок
            try:
                buttons = []
                for char in message.text.split('\n'):
                    if '&&' in char:
                        tmpl = []
                        for i in char.split('&&'):
                            tmpl.append(dict([i.split('-', maxsplit=1)]))
                        buttons.append(tmpl)
                    else:
                        buttons.append(dict([char.split('-', maxsplit=1)]))
                menu = InlineKeyboardMarkup()
                btns_list = []
                items = []
                for row in buttons:
                    if type(row) == dict:
                        url1 = str(list(row.items())[0][1]).strip()
                        text1 = list(row.items())[0][0]
                        menu.add(InlineKeyboardButton(text=text1, url=url1))
                    else:
                        items.clear()
                        btns_list.clear()
                        for d in row:
                            items.append(list(d.items())[0])
                        for text, url in items:
                            url = url.strip()
                            btns_list.append(InlineKeyboardButton(text=text, url=url))
                        menu.add(*btns_list)
                ###########$##############
                async with state.proxy() as data:
                    data['btns'] = str(menu)
                    media = data['media']
                    text = data['text']
                    Spam_data.make_spam(text, str(menu), str(media))
                    if media != 'None':
                        content_type = media[0]
                        if content_type == 'photo':
                            await message.bot.send_photo(user_id, media[1], caption=text, parse_mode='HTML',
                                                         reply_markup=menu)
                        elif content_type == 'video':
                            await message.bot.send_video(user_id, media[1], caption=text, parse_mode='HTML',
                                                         reply_markup=menu)
                        elif content_type == 'animation':
                            await message.bot.send_animation(user_id, media[1], caption=text, parse_mode='HTML',
                                                             reply_markup=menu)
                    else:
                        await message.answer(text, reply_markup=menu, parse_mode='HTML', disable_web_page_preview=True)

            except Exception as e:
                await message.reply(f'Похоже что непрвильно введена клавиатура')
        else:
            async with state.proxy() as data:
                data['btns'] = 'None'
                media = data['media']
                text = data['text']
                Spam_data.make_spam(text, 'None', str(media))

                if media != 'None':
                    content_type = media[0]
                    if content_type == 'photo':
                        await message.bot.send_photo(user_id, media[1], caption=text, parse_mode='HTML')
                    elif content_type == 'video':
                        await message.bot.send_video(user_id, media[1], caption=text, parse_mode='HTML')
                    elif content_type == 'animation':
                        await message.bot.send_animation(user_id, media[1], caption=text, parse_mode='HTML')
                else:
                    await message.answer(text, parse_mode='HTML', disable_web_page_preview=True)
        await message.answer(f'Пришли команду /sendspam_{Spam_data.select_id()} чтоб начать рассылку')
        await state.finish()


async def start_spam(message: Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    if user_id in config.ADMINS:
        spam_id = int(message.text.replace('/sendspam_', ''))
        text = Spam_data.select_text(spam_id)
        keyboard = Spam_data.select_keyboard(spam_id)
        media = Spam_data.select_media(spam_id)
        if text == 'None':
            text = None
        if keyboard == 'None':
            keyboard = None
        all_user = User_data.get_all_user_id()
        await message.answer(f'Считанно {len(all_user)} пользователей запускаю рассылку')
        no_send = 0
        send = 0
        for user in all_user:
            user = int(user)
            try:
                if media != 'None' and media != None:  # Есть медиа
                    if type(media) is list:
                        await message.bot.send_media_group(user, media)
                    else:
                        content_type = media[0]

                        if content_type == 'photo':
                            await message.bot.send_photo(user, media[1], caption=text, parse_mode='HTML',
                                                         reply_markup=keyboard)
                        elif content_type == 'video':
                            await message.bot.send_video(user, media[1], caption=text, parse_mode='HTML',
                                                         reply_markup=keyboard)
                        elif content_type == 'animation':
                            await message.bot.send_animation(user, media[1], caption=text, parse_mode='HTML',
                                                             reply_markup=keyboard)

                else:  # Нету медиа
                    if keyboard != 'None' and keyboard != None:  # Есть кнопки
                        await message.bot.send_message(chat_id=user, text=text, reply_markup=keyboard,
                                                       parse_mode='HTML', disable_web_page_preview=True)
                    else:
                        await message.bot.send_message(chat_id=user, text=text, parse_mode='HTML',
                                                       disable_web_page_preview=True)
                send += 1
                User_data.active_user(user)

            except:
                no_send += 1
                User_data.disactive_user(user_id)
        await message.answer(f'Рассылка окончена.\n'
                             f'Отправленно: {send} пользователям\n'
                             f'Не отправленно: {no_send} пользователям')




def register_admin(dp: Dispatcher):
    dp.middleware.setup(AlbumMiddleware())
    dp.register_message_handler(stat, commands='stat')
    dp.register_message_handler(spam1, commands='spam', state='*')
    dp.register_message_handler(spam2_media_group, is_media_group=True, content_types=types.ContentType.ANY,
                                state=FSM_ADMIN_SPAM.text)
    dp.register_message_handler(spam2, content_types=['photo', 'video', 'animation', 'text'], state=FSM_ADMIN_SPAM.text)
    dp.register_message_handler(spam3, state=FSM_ADMIN_SPAM.btns, content_types=['text'])
    dp.register_message_handler(start_spam, lambda message: str(message.text).startswith('/sendspam_'), state='*')