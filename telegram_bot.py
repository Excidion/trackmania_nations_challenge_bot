import configparser
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, BaseFilter, Filters, ConversationHandler
from datetime import datetime
import os

from messages import get_ladder_as_html
from plots import timedelta_to_string
from utils import get_player_name, set_account_to_player_mapping

config = configparser.ConfigParser()
config.read("config.ini")
GROUPCHAT_ID = config.get("TELEGRAM_BOT", "GROUPCHAT_ID")

OPENING_MESSAGE = "\n".join([
    "Hello and welcome to our weekly TrackMania Nations Challenge!",
    "I manage most of what is happening on and around the racetrack.\n",
    "There are multiple ways in which I can help you:",
    "Type /commands for a list of commands that I understand.",
    "If you are new to the competition I recommend starting with /register so I know who you are (in game)!"
])



class UserInGroupChatFilter(BaseFilter):
    def filter(self, message):
        id =  message.from_user.id
        status = message.chat.bot.get_chat_member(chat_id=GROUPCHAT_ID, user_id=id).status
        return status in ["creator", "administrator", "member", "restricted"]

class ConversationNotInGroupChatFilter(BaseFilter):
    def filter(self, message):
        chat_id = message.chat.id
        if int(chat_id) == int(GROUPCHAT_ID):
            message.reply_text("I will not do this in public, contact me in a private message.")
            return False # don't handle this conversation in public chat
        else:
            return True




class TelegramBot():
    def __init__(self):
        self.updater = Updater(
            token = config.get("TELEGRAM_BOT", "TOKEN"),
            use_context = True,
        )
        dispatcher = self.updater.dispatcher

        # welcome action
        dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, self.welcome_action))

        # simple commands
        COMMAND_MAP = {
            "chat_id": self.print_chat_id,
            "ladder": self.print_ladder,
            "week": self.print_ladder,
            "total": self.print_plot,
            "graph": self.print_plot,
            "link": self.print_website_link,
        }
        PRIVATE_COMMAND_MAP = {
            "start": self.help,
            "help": self.help,
            "commands": self.print_commands,
            "server": self.print_join_instructions,
        }

        for command in COMMAND_MAP:
            dispatcher.add_handler(
                CommandHandler(
                    command,
                    COMMAND_MAP[command],
                    filters = UserInGroupChatFilter(),
                )
            )

        for command in PRIVATE_COMMAND_MAP:
            dispatcher.add_handler(
                CommandHandler(
                    command,
                    PRIVATE_COMMAND_MAP[command],
                    filters = UserInGroupChatFilter() & ConversationNotInGroupChatFilter(),
                )
            )


        # advanced commands
        dispatcher.add_handler(ConversationHandler(
            entry_points = [
                CommandHandler(
                    "register",
                    self.start_registration,
                    filters = UserInGroupChatFilter() & ConversationNotInGroupChatFilter(),
                )
            ],
            states = {
                0: [MessageHandler(Filters.text, self.store_name)],
                1: [MessageHandler(Filters.text, self.store_account)],
                2: [MessageHandler(Filters.text, self.bool_decision_to_save)]
            },
            fallbacks = [CommandHandler("cancel", self.cancel)]),
        )



    # send this to every user that joins the group
    def welcome_action(self, update, context):
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
        self.updater.bot.send_message(
            chat_id = GROUPCHAT_ID,
            text = "Here are this weeks results!",
        )
        self.updater.bot.send_message(
            chat_id = GROUPCHAT_ID,
            text = get_ladder_as_html(),
            parse_mode = "HTML",
        )
        self.updater.bot.send_message(
            chat_id = GROUPCHAT_ID,
            text = "And this is the influence on the total rankings:",
        )
        path = os.path.join(
            config.get("LOCAL_STORAGE", "plot_dir"),
            config.get("LOCAL_STORAGE", "total_standings")
        )
        with open(path, "rb") as file:
            self.updater.bot.send_photo(
                chat_id = GROUPCHAT_ID,
                photo = file,
            )

        print("Posted results to groupchat.")


    # simple commands
    def help(self, update, context):
        update.message.reply_text(OPENING_MESSAGE)

    def print_chat_id(self, update, context):
        update.message.reply_text(str(update.message.chat_id))

    def print_plot(self, update, context):
        path = os.path.join(
            config.get("LOCAL_STORAGE", "plot_dir"),
            config.get("LOCAL_STORAGE", "total_standings")
        )
        with open(path, "rb") as file:
            update.message.reply_photo(photo=file)

    def print_website_link(self, update, context):
        webserver = config.get("DATA_SOURCES", "WEBSERVER")
        update.message.reply_text(f"https://{webserver}")

    def print_join_instructions(self, update, context):
        server_name  = config.get("GAME_SERVER", "accout")
        pwd = config.get("GAME_SERVER", "password")
        update.message.reply_text("To join the server you have to enter the following link to TrackMania internal browser:")
        update.message.reply_text(f"tmtp://#addfavourite={server_name}")
        update.message.reply_photo(photo=None) # TODO
        update.message.reply_text("This will add the server to your list of favourites.")
        update.message.reply_text(f"The servers password is \"{pwd}\".")

    def print_commands(self, update, context):
        update.message.reply_text(
            "\n".join([
                "These are the commands I know and what they do:",
                "/week - Shows this weeks rankings.",
                "/total - Shows the graph of the total season rankings.",
                "/link - Shows the link to the website.",
                "\nThe following commands can just be handled in private messages with me:",
                "/server - Shows you how to connect to the game server.",
                "/register - Make your name appear in the rankings. Recommended, if you haven't done this yet.",
                "/help - Shows this overview.",
            ])
        )

    def print_ladder(self, update, context):
        # TODO markdown?
        update.message.reply_text(get_ladder_as_html(), parse_mode="HTML")


    # commands for advanced conversations
    def start_registration(self, update, context):
        user_account = update.message.from_user["username"]
        first_name = update.message.from_user["first_name"]
        print(f"{user_account} ({first_name}) started registration.")
        update.message.reply_text(
            text = "\n".join([
                "I will take you through the registration process. You can abort the process anytime via /cancel ",
                "\nTo get started I need your first name.",
                "This name will be displayed on all rankings and graphs.",
            ])
        )
        return 0

    def store_name(self, update, context):
        webserver = config.get("DATA_SOURCES", "WEBSERVER")
        context.user_data["name"] = update.message.text
        update.message.reply_text(
            text = "Next up I need your TrackMania account name.\nYou can see your account name when logging into TrackMania.",
        )
        try:
            update.message.reply_photo(photo=f"https://{webserver}/register_instruction.png")
        except: pass
        return 1

    def store_account(self, update, context):
        account = update.message.text
        context.user_data["account"] = account
        name = context.user_data["name"]
        update.message.reply_text(
            f"I will now link the TrackMania account \"{account}\" to \"{name}\".\nDo you want to proceed?",
            reply_markup = ReplyKeyboardMarkup([["Yes", "No"]], one_time_keyboard=True),
        )
        return 2

    def bool_decision_to_save(self, update, context):
        reply = update.message.text
        if reply.lower() == "yes":
            account = context.user_data["account"]
            name =  context.user_data["name"]
            set_account_to_player_mapping(account, name)
            update.message.reply_text(
                f"TM-Account \"{account}\" has been mapped to \"{name}\".",
                reply_markup = ReplyKeyboardRemove(),
            )
        else:
            update.message.reply_text("Action canceled.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END


    def cancel(self, update, context):
        update.message.reply_text("Action canceled.")
        return ConversationHandler.END




if __name__ == '__main__':

    chatbot = TelegramBot()
    chatbot.start_bot()
    try:
        while True:
            pass
    except KeyboardInterrupt: pass
    chatbot.stop_bot()
