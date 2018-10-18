import configparser
import time
import os
from multiprocessing import Pipe

from utils import load_data, load_medal_times, get_last_SQL_update
from calculations import calculate_complete_data, get_standings
from plots import plot_total_standings, timedelta_to_string
from telegram_bot import TelegramBot




def renew_plot(data):
    year, week = data.dropna()["Date"].max().isocalendar()[0:2]
    plot_total_standings(data, f"Meisterschaftsstand_y{year}_w{week}")

def compare_data_and_create_info_messages(old_data):
    messages = []
    new_data = calculate_complete_data()
    new_entries = new_data[~new_data.isin(old_data)].dropna()
    for row_index, entry in new_entries.iterrows():
        player_name = entry["Player"]
        new_record = timedelta_to_string(entry["Time"])
        track = entry["Track"]
        message = f"{track}: {player_name} scored a new record of {new_record}!"
        messages.append(message)
    return messages




if __name__ == "__main__":

    config = configparser.ConfigParser()
    config.read("config.ini")

    PLOT_DIR = config["SAVE_POINTS"]["PLOT_DIR"]
    if not os.path.exists(PLOT_DIR):
        os.makedirs(PLOT_DIR)

    transmitter, reciever = Pipe()
    chatbot = TelegramBot(reciever)
    chatbot.start_bot()


    while True:
        try:
            last_SQL_update = get_last_SQL_update()
            data = calculate_complete_data()
            renew_plot(data)
            transmitter.send(data) # newest info to bot

            while last_SQL_update == get_last_SQL_update(): # wait until there are new entries to the database
                time.sleep(1) # check every second

            messages = compare_data_and_create_info_messages(data)
            for message in messages:
                print(message)
                chatbot.send_groupchat_message(message)


        except KeyboardInterrupt:
            chatbot.stop_bot() # kill background process
            raise SystemExit

        except Exception as e:
            print(e)
