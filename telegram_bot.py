import configparser
from telegram.ext import Updater, CommandHandler
import logging

class TelegramBot():
    def __init__(self):
        # base configuration
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.GROUPCHAT_ID = self.config["TELEGRAM_BOT"]["GROUPCHAT_ID"]
        TOKEN = self.config["TELEGRAM_BOT"]["TOKEN"]

        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)

        # bot setup
        self.updater = Updater(token = TOKEN)
        self.jobs = self.updater.job_queue
        dispatcher = self.updater.dispatcher

        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(CommandHandler("id", self.print_chat_id))



    # methods for use in main
    def start_bot(self):
        self.updater.start_polling() # start mainloop

    def stop_bot(self):
        self.updater.stop()

    def send_groupchat_message(self, text):
        self.jobs.run_once(self.send_groupchat_message_job, 0, context = text)

    # associated jobs
    def send_groupchat_message_job(self, bot, job):
        bot.send_message(chat_id = self.GROUPCHAT_ID, text = job.context)


    # commands
    def start(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="Welcome to the Jungle!")

    def print_chat_id(self, bot, update):
        chat_id = update.message.chat_id
        bot.send_message(chat_id = chat_id, text = chat_id)
