import configparser
from telegram.ext import Updater, CommandHandler
import logging

config = configparser.ConfigParser()
config.read("config.ini")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


GROUPCHAT_ID = config["TELEGRAM_BOT"]["GROUPCHAT_ID"]

updater = Updater(token = config["TELEGRAM_BOT"]["TOKEN"])
dispatcher = updater.dispatcher # mainloop process
jobs = updater.job_queue


# methods for use in main
def start_bot():
    updater.start_polling() # start mainloop

def stop_bot():
    updater.stop()

def send_groupchat_message(text):
    jobs.run_once(send_groupchat_message_job, 0, context = text)




# jobs
def send_groupchat_message_job(bot, job):
    bot.send_message(chat_id = GROUPCHAT_ID, text = job.context)




# commands
def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Welcome to the Jungle!")

def print_chat_id(bot, update):
    chat_id = update.message.chat_id
    bot.send_message(chat_id = chat_id, text = chat_id)


start_handler = CommandHandler("start", start)
printId_hanlder = CommandHandler("id", print_chat_id)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(printId_hanlder)
