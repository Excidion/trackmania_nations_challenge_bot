import configparser
from telegram.ext import Updater, CommandHandler
from calculations import get_standings




class TelegramBot():
    def __init__(self, reciever):
        # base configuration
        self.reciever = reciever
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.GROUPCHAT_ID = self.config["TELEGRAM_BOT"]["GROUPCHAT_ID"]
        COMMAND_MAP = {"start": self.start,
                       "id": self.print_chat_id,
                       "ladder": self.print_ladder}

        # bot setup
        self.updater = Updater(token = self.config["TELEGRAM_BOT"]["TOKEN"])
        self.jobs = self.updater.job_queue
        dispatcher = self.updater.dispatcher
        for command in COMMAND_MAP:
            dispatcher.add_handler(CommandHandler(command, COMMAND_MAP[command]))


    # methods for use in main
    def start_bot(self):
        self.updater.start_polling() # start mainloop

    def stop_bot(self):
        self.updater.stop()

    def send_groupchat_message(self, text):
        self.jobs.run_once(self.send_groupchat_message_job, 0, context = text)

    def send_groupchat_message_job(self, bot, job):
        bot.send_message(chat_id = self.GROUPCHAT_ID, text = job.context)


    # commands
    def start(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="Welcome to the Jungle!")

    def print_chat_id(self, bot, update):
        chat_id = update.message.chat_id
        bot.send_message(chat_id = chat_id, text = chat_id)

    def print_ladder(self, bot, update):
        data = self.reciever.recv()
        ladder = list(reversed(get_standings(data).index))
        bot.send_message(chat_id=update.message.chat_id, text="\n".join(ladder))
