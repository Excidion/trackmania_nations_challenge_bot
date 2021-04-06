import configparser
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, BaseFilter, Filters, ConversationHandler
from datetime import datetime
import os
from plots import timedelta_to_string, get_total_standings_plot, get_ladder
from utils import get_player_name, register_player

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
        self.filter_participant = UserInGroupChatFilter()
        self.filter_private_message = UserInGroupChatFilter() & ConversationNotInGroupChatFilter()

        # welcome action
        dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, self.welcome_action))

        # setup commands
        dispatcher.add_handler(CommandHandler("chat_id", self.print_chat_id))

        # simple commands
        COMMAND_MAP = {
            "week": self.print_ladder,
            "total": self.print_plot,
        }
        PRIVATE_COMMAND_MAP = {
            "start": self.help,
            "help": self.help,
            "commands": self.print_commands,
            "server": self.print_join_instructions,
        }
        # commnds that can be executed everywhere
        for command in COMMAND_MAP:
            dispatcher.add_handler(
                CommandHandler(
                    command,
                    COMMAND_MAP[command],
                    filters = self.filter_participant,
                )
            )
        # commands for use in DMs
        for command in PRIVATE_COMMAND_MAP:
            dispatcher.add_handler(
                CommandHandler(
                    command,
                    PRIVATE_COMMAND_MAP[command],
                    filters = self.filter_private_message,
                )
            )

        # registration command
        dispatcher.add_handler(ConversationHandler(
            entry_points = [
                CommandHandler(
                    "register",
                    self.start_registration,
                    filters = self.filter_private_message,
                )
            ],
            states = {
                0: [MessageHandler(Filters.text, self.check_suggestion)],
                1: [MessageHandler(Filters.text, self.store_name)],
                2: [MessageHandler(Filters.text, self.store_account)],
                3: [MessageHandler(Filters.text, self.confirm_link)],
                4: [MessageHandler(Filters.text, self.link_telegram)]
            },
            fallbacks = [CommandHandler("cancel", self.cancel)]),
        )



    # send this to every user that joins the group
    def welcome_action(self, update, context):
        for new_user in update.message.new_chat_members:
            self.updater.bot.send_message(chat_id=new_user.id, text=OPENING_MESSAGE)



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
            text = get_ladder(),
            parse_mode = "HTML",
        )
        self.updater.bot.send_message(
            chat_id = GROUPCHAT_ID,
            text = "And this is the influence on the total rankings:",
        )
        self.updater.bot.send_photo(
            chat_id = GROUPCHAT_ID,
            photo = get_total_standings_plot(),
        )
        print("Posted results to groupchat.")


    # simple commands
    def help(self, update, context):
        update.message.reply_text(OPENING_MESSAGE)

    def print_chat_id(self, update, context):
        update.message.reply_text(str(update.message.chat_id))

    def print_plot(self, update, context):
        update.message.reply_photo(photo=get_total_standings_plot())


    def print_join_instructions(self, update, context):
        server_name  = config.get("GAME_SERVER", "account")
        pwd = config.get("GAME_SERVER", "password")
        update.message.reply_text("To join the server you have to enter the following link to TrackMania internal browser:")
        with open("instructions/ingame_browser.png", "rb") as file:
            update.message.reply_photo(photo=file)
        with open("instructions/add_server.png", "rb") as file:
            update.message.reply_photo(photo=file)
        update.message.reply_text(f"tmtp://#addfavourite={server_name}")
        update.message.reply_text("This will add the server to your list of favourites.")
        update.message.reply_text(f"The servers password is \"{pwd}\".")

    def print_commands(self, update, context):
        update.message.reply_text(
            "\n".join([
                "These are the commands I know and what they do:",
                "/week - Shows this weeks rankings.",
                "/total - Shows the graph of the total season rankings.",
                "\nThe following commands can just be handled in private messages with me:",
                "/server - Shows you how to connect to the game server.",
                "/register - Make your name appear in the rankings. Recommended, if you haven't done this yet.",
                "/help - Shows this overview.",
            ])
        )

    def print_ladder(self, update, context):
        update.message.reply_text(get_ladder(), parse_mode="HTML")


    # commands for advanced conversations
    def start_registration(self, update, context):
        first_name = update.message.from_user["first_name"]
        context.user_data["first_name"] = first_name
        context.user_data["telegram_id"] = update.message.from_user["id"]
        update.message.reply_text(
            text = "\n".join([
                "I will take you through the registration process. You can abort the process anytime via /cancel ",
                "\nTo get started I need your first name.",
                "This name will be displayed on all rankings and graphs.",
            ])
        )
        update.message.reply_text(
            f"Let me guess, you are {first_name}, right?",
            reply_markup = ReplyKeyboardMarkup(
                [[f"Yes, that's me!", "No, use another name."]],
                one_time_keyboard = True,
                )
        )
        return 0

    def check_suggestion(self, update, context):
        reply = update.message.text.split(",")[0].lower()
        if reply == "yes":
            context.user_data["name"] = context.user_data["first_name"]
            update.message.reply_text(
                text = "Next up I need your TrackMania account name.\nYou can see your account name when logging into TrackMania.",
                reply_markup = ReplyKeyboardRemove(),
            )
            with open("instructions/account_name.png", "rb") as file:
                update.message.reply_photo(photo=file)
            return 2
        else:
            update.message.reply_text(
                text = "What's your first name then?",
                reply_markup = ReplyKeyboardRemove(),
            )
            return 1


    def store_name(self, update, context):
        context.user_data["name"] = update.message.text
        update.message.reply_text(
            text = "Next up I need your TrackMania account name.\nYou can see your account name when logging into TrackMania.",
            reply_markup = ReplyKeyboardRemove(),
        )
        with open("instructions/account_name.png", "rb") as file:
            update.message.reply_photo(photo=file)
        return 2

    def store_account(self, update, context):
        account = update.message.text
        context.user_data["account"] = account
        name = context.user_data["name"]
        update.message.reply_text(
            f"I will now link the TrackMania account \"{account}\" to \"{name}\".\nDo you want to proceed?",
            reply_markup = ReplyKeyboardMarkup([["Yes", "No"]], one_time_keyboard=True),
        )
        return 3

    def confirm_link(self, update, context):
        reply = update.message.text
        if reply.lower() == "yes":
            update.message.reply_text(
                f"One last thing: Do you want me to remember your Telegram account? This way I can reach you whenever there is something relevant to you.",
                reply_markup = ReplyKeyboardMarkup(
                    [["Yes", "No"]],
                    one_time_keyboard =True
                    ),
            )
            return 4
        else:
            update.message.reply_text("Action canceled.", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

    def link_telegram(self, update, context):
        account = context.user_data["account"]
        name =  context.user_data["name"]
        reply_text = f"TM-Account \"{account}\" has been linked to \"{name}\""
        if update.message.text.lower() == "yes":
            telegram_id = context.user_data["telegram_id"]
            register_player(account, name, telegram_id)
            reply_text += " and your telegram account."
        else:
            register_player(accout, name)
            reply_text += ". Telegram account has not been linked."
        update.message.reply_text(
            reply_text,
            reply_markup = ReplyKeyboardRemove(),
        )
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
