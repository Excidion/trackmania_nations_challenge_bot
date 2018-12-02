import configparser
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, BaseFilter, Filters, ConversationHandler
from datetime import datetime

from messages import get_ladder_as_html
from plots import timedelta_to_string
from utils import get_player_name, set_account_to_player_mapping

config = configparser.ConfigParser()
config.read("config.ini")
GROUPCHAT_ID = config["TELEGRAM_BOT"]["GROUPCHAT_ID"]

OPENING_MESSAGE = "\n".join([
    "Hello and welcome to our weekly TrackMania Nations Challenge!",
    "I manage most of what is happening on and around the racetrack.\n",
    "There are multiple ways in which I can help you:",
    "Type /commands for a list of commands that I understand.",
    "If you are new to the competition I recommend starting with /register so I know who you are (in game)!"])



class UserInGroupChatFilter(BaseFilter):
    def filter(self, message):
        id =  message.from_user.id
        status = message.chat.bot.get_chat_member(chat_id=GROUPCHAT_ID, user_id=id).status
        return status in ["creator", "administrator", "member", "restricted"]

class ConversationNotInGroupChatFilter(BaseFilter):
    def filter(self, message):
        chat_id = message.chat.id
        if int(chat_id) == int(GROUPCHAT_ID):
            message.chat.bot.send_message(chat_id = chat_id,
                                          text = "I will not do this in public, contact me in a private message.")
            return False # don't handle this conversation in public chat
        else:
            return True




class TelegramBot():
    def __init__(self):
        # bot setup
        self.updater = Updater(token = config["TELEGRAM_BOT"]["TOKEN"])
        self.jobs = self.updater.job_queue
        dispatcher = self.updater.dispatcher

        # welcome action
        dispatcher.add_handler(MessageHandler(
            Filters.status_update.new_chat_members,
            self.welcome_action))

        # simple commands
        COMMAND_MAP = {"chat_id": self.print_chat_id,
                       "ladder": self.print_ladder,
                       "graph": self.print_plot_link,
                       "link": self.print_website_link}
        PRIVATE_COMMAND_MAP = {"start": self.help,
                               "help": self.help,
                               "commands": self.print_commands,
                               "server": self.print_join_instructions}


        for command in COMMAND_MAP:
            dispatcher.add_handler(CommandHandler(command,
                                                  COMMAND_MAP[command],
                                                  filters = UserInGroupChatFilter()))
        for command in PRIVATE_COMMAND_MAP:
            dispatcher.add_handler(CommandHandler(command,
                                                  PRIVATE_COMMAND_MAP[command],
                                                  filters = (UserInGroupChatFilter() and
                                                  ConversationNotInGroupChatFilter())))


        # advanced commands
        dispatcher.add_handler(ConversationHandler(
            entry_points = [CommandHandler("register", self.start_registration,
                                           filters = (UserInGroupChatFilter() and
                                                      ConversationNotInGroupChatFilter()))],
            states = {0: [MessageHandler(Filters.text,
                                         self.store_name,
                                         pass_user_data=True)],
                      1: [MessageHandler(Filters.text,
                                         self.store_account,
                                         pass_user_data=True)],
                      2: [MessageHandler(Filters.text,
                                       self.bool_decision_to_save,
                                       pass_user_data=True)]},
            fallbacks = [CommandHandler("cancel", self.cancel)]))



    # send this to every user that joins the group
    def welcome_action(self, bot, update):
        for new_user in update.message.new_chat_members:
            bot.send_message(chat_id=new_user.id, text=OPENING_MESSAGE)



    # methods for use in main
    def start_bot(self):
        self.updater.start_polling() # start mainloop
        print("Startup successfull. Telegram-Bot is now online.")

    def stop_bot(self):
        print("Shutdown initiated.")
        self.updater.stop()

    def send_groupchat_message(self, text):
        print("Posted to Groupchat:", text)
        self.updater.bot.send_message(chat_id=GROUPCHAT_ID, text=text)

    def send_results_to_groupchat(self):
        webserver = config["DATA_SOURCES"]["PLAYER_DATA"]
        filename = config["SAVE_POINTS"]["CURRENT_PLOT"]
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # timestamp to avoid using cached old thumbnails
        message = get_ladder_as_html()

        bot.send_message(chat_id = GROUPCHAT_ID,
                         text = message,
                         parse_mode = "HTML")
        bot.send_photo(chat_id = update.message.chat_id,
                       photo = f"https://{webserver}/{filename}.png?a={ts}")
        print("Posted results to groupchat.")


    # simple commands
    def help(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text=OPENING_MESSAGE)

    def print_chat_id(self, bot, update):
        chat_id = update.message.chat_id
        bot.send_message(chat_id = chat_id, text = chat_id)

    def print_plot_link(self, bot, update):
        webserver = config["DATA_SOURCES"]["PLAYER_DATA"]
        filename = config["SAVE_POINTS"]["CURRENT_PLOT"]
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # timestamp to avoid using cached old thumbnails
        bot.send_photo(chat_id = update.message.chat_id,
                       photo = f"https://{webserver}/{filename}.png?a={ts}")

    def print_website_link(self, bot, update):
        webserver = config["DATA_SOURCES"]["PLAYER_DATA"]
        bot.send_message(chat_id = update.message.chat_id,
                         text = f"https://{webserver}")

    def print_join_instructions(self, bot, update):
        webserver = config["DATA_SOURCES"]["PLAYER_DATA"]
        server_name = config["DATA_SOURCES"]["TM_SERVER_NAME"]
        pwd = config["DATA_SOURCES"]["TM_SERVER_PWD"]
        id = update.message.chat_id
        bot.send_message(chat_id=id, text="To join the server you have to enter the following link to TrackMania internal browser:")
        bot.send_message(chat_id=id, text=f"tmtp://#addfavourite={server_name}")
        bot.send_photo(chat_id=id, photo=f"https://{webserver}/tm_browser.png")
        bot.send_photo(chat_id=id, photo=f"https://{webserver}/tm_addfavo.png")
        bot.send_message(chat_id=id, text="This will add the server to your list of favourites.")
        bot.send_message(chat_id=id, text=f"The servers password is \"{pwd}\".")

    def print_commands(self, bot, update):
        message = "\n".join(["These are the commands I know and what they do:",
                             "/ladder - Shows this weeks rankings.",
                             "/graph - Shows the current total rankings.",
                             "/link - Shows the link to the website.",
                             "\nThe following commands can just be handled in private messages with me:",
                             "/server - Shows you how to connect to the game server.",
                             "/register - Make your name appear in the rankings. Recommended, if you haven't done this yet."])

        bot.send_message(chat_id = update.message.chat_id,
                         text = message)


    def print_ladder(self, bot, update):
        message = get_ladder_as_html()
        bot.send_message(chat_id = update.message.chat_id,
                         text = message,
                         parse_mode = "HTML")


    # commands for advanced conversations
    def start_registration(self, bot, update):
        user_account = update.message.from_user["username"]
        first_name = update.message.from_user["first_name"]
        print(f"{user_account} ({first_name}) started registration.")
        bot.send_message(chat_id = update.message.chat_id,
                         text = "\n".join(["I will take you through the registration process. You can abort the process anytime via /cancel ",
                                           "\nTo get started I need your first name.",
                                           "This name will be displayed on all rankings and graphs."]))
        return 0

    def store_name(self, bot, update, user_data):
        webserver = config["DATA_SOURCES"]["PLAYER_DATA"]
        user_data["name"] = update.message.text
        bot.send_message(chat_id = update.message.chat_id,
                         text = "\n".join(["Next up I need your TrackMania account name.",
                                           "You can see your account name when logging into TrackMania."]))
        bot.send_photo(chat_id = update.message.chat_id,
                       photo = f"https://{webserver}/register_instruction.png")
        return 1

    def store_account(self, bot, update, user_data):
        account = update.message.text
        user_data["account"] = account
        name = user_data["name"]
        bot.send_message(chat_id = update.message.chat_id,
                         text = f"I will now link the TrackMania account \"{account}\" to \"{name}\".\nDo you want to proceed?",
                         reply_markup = ReplyKeyboardMarkup([["Yes", "No"]], one_time_keyboard=True))

        return 2

    def bool_decision_to_save(self, bot, update, user_data):
        reply = update.message.text
        if reply.lower() == "yes":
            account = user_data["account"]
            name =  user_data["name"]
            set_account_to_player_mapping(account, name)
            update.message.reply_text(f"TM-Account \"{account}\" has been mapped to \"{name}\".",
                                      reply_markup=ReplyKeyboardRemove())
        else:
            update.message.reply_text("Action canceled.",
                                      reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END



    def cancel(self, bot, update):
        update.message.reply_text("Action canceled.")
        return ConversationHandler.END
