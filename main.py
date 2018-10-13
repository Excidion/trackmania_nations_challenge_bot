import configparser
import time
import os

from utils import load_data, load_medal_times, get_last_SQL_update
from calculations import get_individual_records, substitute_missing_times, sort_by_track_and_tracks_by_date, get_standings
from plots import plot_total_standings


def update_data():
    raw_data = load_data()
    individual_records = get_individual_records(raw_data)
    data = substitute_missing_times(individual_records, nadeo_medals)
    data = sort_by_track_and_tracks_by_date(data)
    year, week = data.dropna()["Date"].max().isocalendar()[0:2]
    plot_total_standings(data, f"Meisterschaftsstand_y{year}_w{week}")
    return data




if __name__ == "__main__":

    config = configparser.ConfigParser()
    config.read("config.ini")

    if not os.path.exists(config["SAVE_POINTS"]["PLOT_DIR"]):
        os.makedirs(config["SAVE_POINTS"]["PLOT_DIR"])

    nadeo_medals = load_medal_times()
    last_SQL_update = get_last_SQL_update()

    data = update_data()


    while True:

        time.sleep(1) # give me some rest
        if last_SQL_update == get_last_SQL_update():
            continue

        print("A new time was set!")
        last_SQL_update = get_last_SQL_update()

        data = update_data()
