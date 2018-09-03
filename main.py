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
ASPECT_RATIO, CANVAS_SIZE, SEND_PHOTO = range(3)
PREFIX = 'brd_'
JPEG_QUALITY = 100
data = {}


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

    reply_keyboard = [['1/1', '4/5', '16/9'],['9/16', '9/19', '2/1']]
    update.message.reply_text('What aspect ratio are you looking for?', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return ASPECT_RATIO


def aspect_ratio(bot, update):
    user = update.message.from_user
    user_id = update.message.from_user.id
    global data

    data[user_id] = {"ar": update.message.text}

    logger.info("Aspect ratio for %s: %s", user.username, update.message.text)

    reply_keyboard = [['1', '1.02', '1.05'],['1.1', '1.2', '1.3']]
    update.message.reply_text('How large do you want your canvas to be?', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return CANVAS_SIZE


def canvas_size(bot, update):
    user = update.message.from_user
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    logger.info("Canvas size for %s: %s", user.username, update.message.text)

    global data

    data[user_id]["cs"] = update.message.text

    ar = eval(data[user_id]["ar"])
    cs = float(data[user_id]["cs"])

    filename = str(user_id) + '.jpeg'

    pic = borderify(filename, ar, cs, (255, 255, 255))

    pic.save(os.path.join(PREFIX+filename), 'JPEG', quality=JPEG_QUALITY, optimize=True)
    bot.send_document(chat_id=chat_id, document=open((PREFIX + filename), 'rb'))

    delete_pictures(update)

    return ConversationHandler.END


def cancel(bot, update):
    user = update.message.from_user
    user_id = update.message.from_user.id

    logger.info("User %s canceled the conversation.", user.username)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def delete_pictures(update):
    chat_id = update.message.chat.id
    filename = str(chat_id) + '.jpeg'

    os.remove(filename)
    os.remove((PREFIX + filename))


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
            ASPECT_RATIO: [RegexHandler('^(1/1|4/5|16/9|9/16|9/19|2/1)$', aspect_ratio)],

            CANVAS_SIZE: [RegexHandler('^(1|1.02|1.05|1.1|1.2|1.3)$', canvas_size)]
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
    updater.idle()


if __name__ == '__main__':
    main()
