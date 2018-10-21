import configparser
import time
import os

from utils import load_data, load_medal_times, get_last_SQL_update, get_player_name
from calculations import calculate_complete_data, get_standings, get_current_track_data
from plots import plot_total_standings, timedelta_to_string
from telegram_bot import TelegramBot




def renew_plot(data):
    year, week = data.dropna()["Date"].max().isocalendar()[0:2]
    plot_total_standings(data, f"Meisterschaftsstand_y{year}_w{week}")

def compare_data_and_create_info_messages(old_data):
    new_data = calculate_complete_data()
    messages = []
    messages += info_about_new_times(old_data, new_data)
    messages += info_about_current_weeks_ladder_changes(old_data, new_data)
    return messages


def info_about_current_weeks_ladder_changes(old_data, new_data):
    messages = []

    new_data = get_current_track_data(new_data)
    old_data = get_current_track_data(old_data)

    new_ladder = get_standings(new_data)
    old_ladder = get_standings(old_data)

    try:
        changes = new_ladder.index != old_ladder.index
    except ValueError: # a new player is in the database.
        new_players = list(set(new_ladder.index) - set(old_ladder.index))
        new_ladder = new_ladder.loc[~new_ladder.index.isin(new_players)] # ignore his first entries.
        changes = new_ladder.index != old_ladder.index

    new_ladder = new_ladder[changes].reset_index().reset_index().set_index("Player")
    old_ladder = old_ladder[changes].reset_index().reset_index().set_index("Player")
    new_ladder["index_change"] = new_ladder["index"] - old_ladder["index"]

    for player in new_ladder.index.values:
        overtakes = new_ladder.loc[player, "index_change"]
        if overtakes > 0:
            index = new_ladder.loc[player, "index"]
            overtook = new_ladder[(new_ladder["index"] >= index-overtakes) & (new_ladder["index"] < index)].index.values
            have_scored = old_data.loc[old_data["Origin"] == "Player", "Player"].unique()
            overtook = [get_player_name(p) for p in overtook if p in have_scored]
            new_record = new_data.groupby(["Player", "Track"])["Time"].min().loc[player, current_track]
            messages.append(f"{get_player_name(player)} scored a {timedelta_to_string(new_record)} and overtook { ', '.join(overtook)}.")

    return messages


def info_about_new_times(old_data, new_data):
    messages = []
    new_entries_index = new_data[~new_data.isin(old_data)].dropna(how="all").index
    new_entries = new_data.loc[new_entries_index]
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

    chatbot = TelegramBot()
    chatbot.start_bot()


    while True:
        try:
            last_SQL_update = get_last_SQL_update()
            data = calculate_complete_data()
            renew_plot(data)

            while last_SQL_update == get_last_SQL_update(): # wait until there are new entries to the database
                time.sleep(1) # check every second

            messages = compare_data_and_create_info_messages(data)
            for message in messages:
                chatbot.send_groupchat_message(message)


        except KeyboardInterrupt:
            chatbot.stop_bot() # kill background process
            raise SystemExit

        except Exception as e:
            print(e)
