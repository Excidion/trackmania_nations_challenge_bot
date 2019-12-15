import configparser
from time import sleep
import os
from datetime import datetime
from multiprocessing import Process

from utils import get_last_SQL_update, get_player_name
from calculations import calculate_complete_data, get_current_track_data
from plots import plot_total_standings, timedelta_to_string
from telegram_bot import TelegramBot
import messages




def main():
    config = configparser.ConfigParser()
    config.read("config.ini")

    PLOT_DIR = config.get("LOCAL_STORAGE", "plot_dir")
    if not os.path.exists(PLOT_DIR):
        os.makedirs(PLOT_DIR)

    chatbot = TelegramBot()
    chatbot.start_bot()
    procs = [Process(target=p, args=[chatbot]) for p in [weekly_results_process, live_updates_process]]
    [p.start() for p in procs]

    try:
        while True:
            pass
    except KeyboardInterrupt:
        # kill background proces
        [p.kill() for p in procs]
        chatbot.stop_bot()
        raise SystemExit


def weekly_results_process(chatbot):
    current_week = get_week_number()
    while not sleep(1):
        if not current_week == get_week_number():
            current_week = get_week_number()
            chatbot.send_groupchat_message("Rien ne va plus!")
            chatbot.send_results_to_groupchat()

def get_week_number():
    return datetime.now().isocalendar()[1]


def live_updates_process(chatbot):
    while True:
        last_SQL_update = get_last_SQL_update()
        data = calculate_complete_data()
        renew_plot(data)
        data.to_pickle("x.p")
        # wait until there are new entries to the database
        while last_SQL_update == get_last_SQL_update():
            sleep(1) # check every second
        # create and send messages based on changes
        for message in compare_data_and_create_info_messages(data):
            chatbot.send_groupchat_message(message)

def renew_plot(data):
    year, week = data.dropna()["Date"].max().isocalendar()[0:2]
    plot_total_standings(data, backup_name=f"standings_y{year}_w{week}")

def compare_data_and_create_info_messages(old_data):
    new_data = calculate_complete_data()
    text = [
        messages.info_about_current_weeks_ladder_changes(old_data, new_data),
    ]
    return text




if __name__ == "__main__":
    main()
