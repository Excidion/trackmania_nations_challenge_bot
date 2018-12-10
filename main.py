import configparser
import time
import os
from datetime import datetime

from utils import load_data, load_medal_times, get_last_SQL_update, get_player_name
from calculations import calculate_complete_data, get_standings, get_current_track_data
from plots import plot_total_standings, timedelta_to_string
from telegram_bot import TelegramBot
import messages



def renew_plot(data):
    year, week = data.dropna()["Date"].max().isocalendar()[0:2]
    plot_total_standings(data, f"Meisterschaftsstand_y{year}_w{week}")
    create_ladder_csv(data)

def create_ladder_csv(data):
    current_track = get_current_track_data(data)
    current_track = current_track[current_track["Origin"] == "Player"]
    current_track.sort_values("Time", inplace=True)
    current_track["Player"] = current_track["Player"].apply(get_player_name)
    current_track["Interval"] = current_track["Time"].diff().apply(timedelta_to_string, add_plus=True)
    current_track["Time"] = current_track["Time"].apply(timedelta_to_string)
    current_track[["Player", "Time", "Interval"]].to_csv("ladder.csv", index=False, header=False)


def compare_data_and_create_info_messages(old_data):
    new_data = calculate_complete_data()
    text = []
    #text += messages.info_about_new_times(old_data, new_data)
    text += messages.info_about_current_weeks_ladder_changes(old_data, new_data)
    return text




if __name__ == "__main__":

    config = configparser.ConfigParser()
    config.read("config.ini")

    PLOT_DIR = config["SAVE_POINTS"]["PLOT_DIR"]
    if not os.path.exists(PLOT_DIR):
        os.makedirs(PLOT_DIR)

    current_week = datetime.now().isocalendar()[1]

    chatbot = TelegramBot()
    chatbot.start_bot()


    while True:
        try:
            last_SQL_update = get_last_SQL_update()
            data = calculate_complete_data()
            renew_plot(data)

            while last_SQL_update == get_last_SQL_update(): # wait until there are new entries to the database
                time.sleep(1) # check every second

                if not current_week == datetime.now().isocalendar()[1]:
                    chatbot.send_groupchat_message("Rien ne va plus!")
                    chatbot.send_results_to_groupchat()
                    current_week = datetime.now().isocalendar()[1]
                    break


            for message in compare_data_and_create_info_messages(data):
                chatbot.send_groupchat_message(message)


        except KeyboardInterrupt:
            chatbot.stop_bot() # kill background process
            raise SystemExit

        except Exception as e:
            print(e)
