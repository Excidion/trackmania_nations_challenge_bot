import configparser
import time
import os

from utils import load_data, load_medal_times, get_last_SQL_update, get_player_name
from calculations import calculate_complete_data, get_standings, get_current_track_data
from plots import plot_total_standings, timedelta_to_string
from telegram_bot import TelegramBot
import messages



def renew_plot(data):
    year, week = data.dropna()["Date"].max().isocalendar()[0:2]
    plot_total_standings(data, f"Meisterschaftsstand_y{year}_w{week}")

def compare_data_and_create_info_messages(old_data):
    new_data = calculate_complete_data()
    messages = []
    messages += messages.info_about_new_times(old_data, new_data)
    messages += messages.info_about_current_weeks_ladder_changes(old_data, new_data)
    return messages




if __name__ == "__main__":

    config = configparser.ConfigParser()
    config.read("config.ini")

    PLOT_DIR = config["SAVE_POINTS"]["PLOT_DIR"]
    if not os.path.exists(PLOT_DIR):
        os.makedirs(PLOT_DIR)

    chatbot = TelegramBot()
    chatbot.start_bot()


    while True:
        try:
            last_SQL_update = get_last_SQL_update()
            data = calculate_complete_data()
            renew_plot(data)

            while last_SQL_update == get_last_SQL_update(): # wait until there are new entries to the database
                time.sleep(1) # check every second

            for message in compare_data_and_create_info_messages(data):
                chatbot.send_groupchat_message(message)


        except KeyboardInterrupt:
            chatbot.stop_bot() # kill background process
            raise SystemExit

        except Exception as e:
            print(e)
