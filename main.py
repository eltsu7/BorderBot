#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to reply to Telegram messages
# This program is dedicated to the public domain under the CC0 license.
"""
This Bot uses the Updater class to handle the bot.

First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)
import logging
from PIL import Image
import os
import json

ASPECT_RATIO, CANVAS_SIZE, SEND_PHOTO, CUSTOM_AR, CUSTOM_CS = range(5)
PREFIX = 'brd_'
JPEG_QUALITY = 100
data = {}
ASPECT_KEYBOARD = [['1/1', '4/5', '16/9'],['9/16', '9/19', 'Custom']]
CANVAS_KEYBOARD = [['1', '1.02', '1.05'],['1.1', '1.2', 'Custom']]
ASPECT_QUESTION = 'What aspect ratio are you looking for? \nYou can always /cancel.'
CANVAS_QUESTION = 'How large do you want your canvas to be? \nYou can always /cancel.'

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

SETTINGS = file_read("settings.json")


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Hello! Send me an uncompressed picture!")


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


def photo(bot, update):
    user = update.message.from_user
    user_id = update.message.from_user.id
    logger.info("%s sent a photo", user.username)

    photo_file = bot.get_file(update.message.document.file_id)
    photo_file.download(str(user_id) + '.jpeg')

    reply_keyboard = ASPECT_KEYBOARD
    update.message.reply_text(ASPECT_QUESTION, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return ASPECT_RATIO


def aspect_ratio(bot, update):

    if update.message.text == "Custom":
        bot.send_message(chat_id=update.message.chat_id, text='Give me an aspect ratio in this from: "a/b". '
                                                            'The value must be between 1/5 and 5/1. \n'
                                                            'You can always /cancel.')
        return CUSTOM_AR

    user_id = update.message.from_user.id
    text = update.message.text
    global data

    a, b = text.split("/")
    ar = float(int(a)/int(b))

    data[user_id] = {"ar": ar}
    move_to_canvas(bot, update)
    return CANVAS_SIZE


def custom_ar(bot, update):
    user_id = update.message.from_user.id

    try:
        text = update.message.text

        a, b = text.split("/")
        ar = float(int(a)/int(b))

        if 0.2 <= ar <= 5:
            data[user_id] = {"ar": ar}

        else:
            raise ValueError

    except (ValueError, TypeError):
        bot.send_message(chat_id=update.message.chat_id, text='Incorrect value. You have to pick a value between 1/5 and 5/1.')
        return CUSTOM_AR

    move_to_canvas(bot, update)
    return CANVAS_SIZE



def move_to_canvas(bot, update):
    user = update.message.from_user
    logger.info("Aspect ratio for %s: %s", user.username, update.message.text)

    update.message.reply_text(CANVAS_QUESTION, reply_markup=ReplyKeyboardMarkup(CANVAS_KEYBOARD, one_time_keyboard=True))


def canvas_size(bot, update):
    user = update.message.from_user
    user_id = update.message.from_user.id
    logger.info("Canvas size for %s: %s", user.username, update.message.text)

    if update.message.text == "Custom":
        bot.send_message(chat_id=update.message.chat_id, text='Give me your desired canvas size. '
                                                            'The value must be between 0 and 3. \n'
                                                            'You can always /cancel.')
        return CUSTOM_CS

    global data
    data[user_id]["cs"] = update.message.text

    send_photo(bot,update)
    return ConversationHandler.END


def custom_cs(bot, update):
    user_id = update.message.from_user.id
    text = update.message.text
    global data

    try:
        cs = float(text)

        if 0 <= cs <= 3:
            data[user_id]["cs"] = text
        else:
            raise ValueError

    except (ValueError, TypeError):
            bot.send_message(chat_id=update.message.chat_id, text='Incorrect value. You have to pick a value between 0 and 3.')
            return CUSTOM_CS

    send_photo(bot, update)
    return ConversationHandler.END


def send_photo(bot, update):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id

    update.message.reply_text("Thanks! This will take a few seconds :).", reply_markup=ReplyKeyboardRemove())

    ar = float(data[user_id]["ar"])
    cs = float(data[user_id]["cs"])

    filename = str(user_id) + '.jpeg'

    pic = borderify(filename, ar, cs, (255, 255, 255))

    pic.save(os.path.join(PREFIX+filename), 'JPEG', quality=JPEG_QUALITY, optimize=True)
    bot.send_document(chat_id=chat_id, document=open((PREFIX + filename), 'rb'))

    delete_data(update)


def cancel(bot, update):
    user = update.message.from_user

    logger.info("User %s canceled the conversation.", user.username)
    update.message.reply_text("See you later! I've deleted everything you've sent me. :)", reply_markup=ReplyKeyboardRemove())

    delete_data(update)

    return ConversationHandler.END


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def delete_data(update):
    user_id = update.message.from_user.id

    global data
    if user_id in data:
        del data[user_id]

    chat_id = update.message.chat.id
    filename = str(chat_id) + '.jpeg'

    os.remove(filename)

    try:
        os.remove((PREFIX + filename))
    except FileNotFoundError:
        pass


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(SETTINGS["tg_token"])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states ASPECT_RATIO, CANVAS_SIZE, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.document, photo)],

        states={
            # TODO custom values
            ASPECT_RATIO: [RegexHandler('^(1/1|4/5|16/9|9/16|9/19|Custom)$', aspect_ratio)],

            CUSTOM_AR: [MessageHandler(Filters.text, custom_ar)],

            CANVAS_SIZE: [RegexHandler('^(1|1.02|1.05|1.1|1.2|Custom)$', canvas_size)],

            CUSTOM_CS: [MessageHandler(Filters.text, custom_cs)],

        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('start', start))


    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    # updater.idle()


if __name__ == '__main__':
    main()
