import configparser
import time
import os

from utils import load_data, load_medal_times, get_last_SQL_update
from calculations import calculate_complete_data, get_standings
from plots import plot_total_standings, timedelta_to_string
from telegram_bot import start_bot, stop_bot, send_groupchat_message




def renew_plot(data):
    year, week = data.dropna()["Date"].max().isocalendar()[0:2]
    plot_total_standings(data, f"Meisterschaftsstand_y{year}_w{week}")




if __name__ == "__main__":

    config = configparser.ConfigParser()
    config.read("config.ini")

    data = calculate_complete_data()

    PLOT_DIR = config["SAVE_POINTS"]["PLOT_DIR"]
    if not os.path.exists(PLOT_DIR):
        os.makedirs(PLOT_DIR)
    renew_plot(data)


    start_bot()
    last_SQL_update = get_last_SQL_update()
    print("Startup successfull. Charlie Whiting is now online.")


    while True:
        try:
            time.sleep(1)

            if last_SQL_update == get_last_SQL_update():
                continue

            last_SQL_update = get_last_SQL_update()


            new_data = calculate_complete_data()
            new_entries = new_data[new_data["Time"] != data["Time"]].dropna()
            for entry in new_entries.iterrows():
                player_name = entry[1]["Player"]
                new_record = timedelta_to_string(entry[1]["Time"])
                message = f"{player_name} scored a new record of {new_record}!"
                print(message)
                send_groupchat_message(message)


            data = new_data.copy()
            renew_plot(data)

        except KeyboardInterrupt:
            print("Shutdown initiated.")
            stop_bot() # kill background process
            raise SystemExit

        except Exception as e:
            print(e)
