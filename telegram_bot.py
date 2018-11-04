import configparser
from telegram.ext import Updater, CommandHandler, MessageHandler, BaseFilter, Filters

from calculations import get_standings, calculate_complete_data, get_current_track_data
from plots import timedelta_to_string
from utils import get_player_name

config = configparser.ConfigParser()
config.read("config.ini")
GROUPCHAT_ID = config["TELEGRAM_BOT"]["GROUPCHAT_ID"]




class InGroupChatFilter(BaseFilter):
    def filter(self, message):
        id =  message.from_user.id
        status = message.chat.bot.get_chat_member(chat_id=GROUPCHAT_ID, user_id=id).status
        return status in ["creator", "administrator", "member", "restricted"]




class TelegramBot():
    def __init__(self):
        # bot setup
        self.GROUPCHAT_ID = GROUPCHAT_ID
        self.updater = Updater(token = config["TELEGRAM_BOT"]["TOKEN"])
        self.jobs = self.updater.job_queue
        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, self.welcome_action))
        COMMAND_MAP = {"start": self.help,
                       "help": self.help,
                       "chat_id": self.print_chat_id,
                       "ladder": self.print_ladder,
                       "graph": self.print_plot_link}
        for command in COMMAND_MAP:
            dispatcher.add_handler(CommandHandler(command,
                                                  COMMAND_MAP[command],
                                                  filters = InGroupChatFilter()))

    def welcome_action(self, bot, update):
        for new_user in update.message.new_chat_members:
            bot.send_message(chat_id=new_user.id, text="Welcome to the Jungle!")



    # methods for use in main
    def start_bot(self):
        self.updater.start_polling() # start mainloop
        print("Startup successfull. Telegram-Bot is now online.")

    def stop_bot(self):
        print("Shutdown initiated.")
        self.updater.stop()

    def send_groupchat_message(self, text):
        print("Posted to Groupchat:", text)
        self.updater.bot.send_message(chat_id=self.GROUPCHAT_ID, text=text)



    # commands
    def help(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text = "Welcome to the Jungle!")

    def print_chat_id(self, bot, update):
        chat_id = update.message.chat_id
        bot.send_message(chat_id = chat_id, text = chat_id)

    def print_plot_link(self, bot, update):
        bot.send_photo(chat_id = update.message.chat_id,
                       photo = "https://poekelbude.ddns.net/current_standings.png")


    def print_ladder(self, bot, update):
        data = get_current_track_data(calculate_complete_data())
        ladder = get_standings(data)

        message_lines = [data["Track"].unique()[0]]
        for i, player in enumerate(list(reversed(ladder.index))):
            line = f"{i+1}) "
            line += get_player_name(player) + ": "
            line += timedelta_to_string(ladder[player]) + " "
            message_lines.append(line)

        max_linelength = max([len(line) for line in message_lines])
        missing_spaces = [(max_linelength-len(line)) for line in message_lines]
        message_lines = [(":"+spaces*" ").join(line.split(":")) for spaces, line in zip(missing_spaces, message_lines)]

        message = "\n".join(message_lines)
        message = f"<pre>{message}</pre>"
        bot.send_message(chat_id = update.message.chat_id,
                         text = message,
                         parse_mode = "HTML")
