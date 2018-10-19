import configparser
from telegram.ext import Updater, CommandHandler

from calculations import get_standings
from plots import timedelta_to_string
from utils import get_player_name




class TelegramBot():
    def __init__(self, reciever):
        # base configuration
        self.reciever = reciever
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.GROUPCHAT_ID = self.config["TELEGRAM_BOT"]["GROUPCHAT_ID"]

        # bot setup
        self.updater = Updater(token = self.config["TELEGRAM_BOT"]["TOKEN"])
        self.jobs = self.updater.job_queue
        dispatcher = self.updater.dispatcher
        COMMAND_MAP = {"start": self.start,
                       "id": self.print_chat_id,
                       "ladder": self.print_ladder}
        for command in COMMAND_MAP:
            dispatcher.add_handler(CommandHandler(command, COMMAND_MAP[command]))


    # methods for use in main
    def start_bot(self):
        self.updater.start_polling() # start mainloop
        print("Startup successfull. Telegram-Bot is now online.")

    def stop_bot(self):
        print("Shutdown initiated.")
        self.updater.stop()

    def send_groupchat_message(self, text):
        print(text)
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
        ladder = get_standings(data)
        message_lines = []
        for i, player in enumerate(list(reversed(ladder.index))):
            line = f"{i+1}) "
            line += get_player_name(player) + ":  "
            line += timedelta_to_string(ladder[player]) + " "
            line += timedelta_to_string(ladder.diff(-1)[player], add_plus=True)
            message_lines.append(line)
        bot.send_message(chat_id=update.message.chat_id, text="\n".join(message_lines))
