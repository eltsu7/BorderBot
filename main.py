# coding: utf-8

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, BaseFilter, CallbackQueryHandler
import json
import os
import sys
from PIL import Image

PREFIX = 'brd_'
JPEG_QUALITY = 100
DEFAULT_ASPECT_RATIO = 4/5
CANVAS_SIZE = 1.1


def handlers(updater):
    dp = updater.dispatcher

    # Tässä alla oleville komennoille annetaan aina bot ja updater argumenteiksi
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.document, picture))
    dp.add_handler(CommandHandler('custom', custom, pass_args=True))
    dp.add_handler(CallbackQueryHandler(button))

def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Hello! Send me an uncompressed picture!")

def picture(bot, update):
    img_id = update.message.document.file_id
    filename = str(update.message.from_user.id) + '.jpeg'

    imgFile = bot.get_file(img_id)
    imgFile.download(filename)

    keyboard = [[InlineKeyboardButton("1:1", callback_data=1),
                 InlineKeyboardButton("4:5", callback_data=4/5)],
                [InlineKeyboardButton("16:9", callback_data=16/9),
                InlineKeyboardButton("9:16", callback_data=9/16)],
                [InlineKeyboardButton("9:19", callback_data=9/19)]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Select your desired aspect ratio. Canvas size defaults to 1.1.\n'\
                                'You can also give custom values by entering:\n'\
                                '/custom A B C\n'\
                                'where A:B is aspect ratio(e.g. "3 2" = 3:2)\n'\
                                'and C is canvas size(e.g. 1.1)', reply_markup=reply_markup)

def delete_pictures(update):
    chat_id = update.message.chat.id
    filename = str(chat_id) + '.jpeg'

    os.remove(filename)
    os.remove((PREFIX + filename))

def custom(bot, update, args):
    chat_id = update.message.chat.id
    filename = str(chat_id) + '.jpeg'

    print(args)

    try:
        aspect_ratio = float(int(args[0]) / int(args[1]))
        canvas_size = float(args[2])
    except:
        bot.send_message(chat_id=update.message.chat_id, text="Incorrect arguments. Try again.")
        return

    if not 0.2 < aspect_ratio < 5 or not 0 <= canvas_size <= 3:
        bot.send_message(chat_id=update.message.chat_id, text="Too extreme values. Try again.")
        return

    try:
        brd_pic = borderify(filename, aspect_ratio, canvas_size, (255,255,255))
    except:
        bot.send_message(chat_id=update.message.chat_id, text="You need to send me a picture first.")
        return

    brd_pic.save(os.path.join(PREFIX+filename), 'JPEG', quality=JPEG_QUALITY, optimize=True)
    bot.send_document(chat_id=chat_id, document=open((PREFIX + filename), 'rb'))

    delete_pictures(update)


def button(bot, update):
    query = update.callback_query
    chat_id = query.message.chat.id
    filename = str(chat_id) + '.jpeg'
    aspect_ratio = float(query.data)

    bot.edit_message_text(text="This will take just a second...",
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id)

    try:
        brd_pic = borderify(filename, aspect_ratio, CANVAS_SIZE, (255,255,255))
    except:
        bot.edit_message_text(text="You need to send me a picture first.",
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id)
        return
    
    brd_pic.save(os.path.join(PREFIX+filename), 'JPEG', quality=JPEG_QUALITY, optimize=True)
    bot.send_document(chat_id=chat_id, document=open((PREFIX + filename), 'rb'))

    delete_pictures(update)

def borderify(name, aspect_ratio=4/5, margin_ratio=1.1, background_color=(255, 255, 255)):
    base = Image.open(name).convert('RGB')
    base_aspect_ratio = base.size[0]/base.size[1]

    # Onko kuva "pystykuvampi" kuin kohde kuvasuhde
    vertical = base_aspect_ratio < aspect_ratio

    side_with_margin = int(base.size[int(vertical)]*margin_ratio)

    # Määritellään taustan koko
    if vertical:
        bg_size = (int(side_with_margin*aspect_ratio), side_with_margin)
    else:
        bg_size = (side_with_margin, int(side_with_margin/aspect_ratio))

    # Taustaväri
    bg = Image.new('RGB', bg_size, background_color)

    # Keskelle
    img_w, img_h = base.size
    bg_w, bg_h = bg.size
    offset = ((bg_w - img_w) // 2, (bg_h - img_h) // 2)

    bg.paste(base, offset)

    return bg


# Lue JSON-tiedosto
def file_read(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            saved_data = json.load(file)
        file.close()
        return saved_data
    except FileNotFoundError:
        print("Oh dog file not found")
        exit(1)


def main():
    updater = Updater(token=SETTINGS["tg_token"])
    handlers(updater)

    updater.start_polling()

SETTINGS = file_read("settings.json")

main()
