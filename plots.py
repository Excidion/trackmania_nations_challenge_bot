import matplotlib
matplotlib.use("Agg") # fix for running on machine without display
import pandas as pd
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
import configparser

from calculations import get_standings
from utils import get_player_name


config = configparser.ConfigParser()
config.read("config.ini")

PLOT_DIR = config["SAVE_POINTS"]["PLOT_DIR"]
CURRENT_PLOT_NAME = config["SAVE_POINTS"]["CURRENT_PLOT"]


def plot_total_standings(data, filename=None):
        fig, ax = plt.subplots()

        season_standings = get_standings(data)

        # preparing for mutiple bar alignment
        bar_alignment = pd.Series({p:timedelta(0) for p in season_standings.index}, name="Time")

        for track in data["Track"].unique():

            # subset for track, ordered by total times
            track_data = data.loc[data["Track"] == track]
            track_data = track_data.set_index("Player").loc[season_standings.index]


            # colored barplots for each player & track
            bars = ax.barh(y = track_data.index.map(get_player_name),
                           width = track_data["Time"].apply(timedelta.total_seconds),
                           left = bar_alignment.apply(timedelta.total_seconds),
                           color = trackname_to_color(track),
                           edgecolor = "white")
                           #edgecolor = track_standings_to_color(track_data))


            # adding up times of plotted track times for following bar plots alignment
            bar_alignment += track_data["Time"]

            # labeling bars with time information
            for i, bar in enumerate(bars):

                # choose label
                label = timedelta_to_string(track_data["Time"][i]) # calculated time
                if track_data["Origin"][i] != "Player":
                    label = track_data["Origin"][i]


                # label each bar
                ax.text(y = bar.get_y() + bar.get_height()/2,
                        x = bar.get_x() + bar.get_width()/2 ,
                        s = label,
                        horizontalalignment = "center",
                        verticalalignment = "center",
                        color = "white")


            # labeling groups of bars with track names
            ax.text(y = bar.get_y() + bar.get_height()*1.33,
                    x = bar.get_x() + bar.get_width()/2,
                    s = track,
                    color = trackname_to_color(track),
                    rotation = 90,
                    verticalalignment = "bottom",
                    horizontalalignment = "center")


        # plot differences in total time
        for i, bar in enumerate(bars):
            ax.text(y = bar.get_y() + bar.get_height()/2,
                    x = bar.get_x() + bar.get_width(),
                    s = timedelta_to_string(season_standings.diff(-1)[i], add_plus=True),
                    color = "grey",
                    verticalalignment = "center",
                    horizontalalignment = "left")


        # general decorating and layouting
        ax.set_xlabel("Total Time [s]")
        fig.tight_layout()


        # save
        if not filename == None:
            fig.savefig(f"{PLOT_DIR}/{filename}.pdf", bbox_inches = "tight")
        fig.savefig(f"{PLOT_DIR}/{CURRENT_PLOT_NAME}.pdf", bbox_inches = "tight")




def timedelta_to_string(td, add_plus=False):
    if not isinstance(td, timedelta):
        return ""

    hours = int(td.seconds//3600)
    minutes = int(td.seconds//60%60)
    seconds = int(td.seconds-hours*3600-minutes*60)
    milliseconds = int(td.microseconds/10**4)

    if hours > 0:
        string =  f"{hours}:{minutes}:{seconds}.{milliseconds}"
    elif minutes > 0:
        string =  f"{minutes}:{seconds}.{milliseconds}"
    else:
        string =  f"{seconds}.{milliseconds}"

    digits = string.split(":")
    digits = ["0" + d if len(d.split(".")[0])==1 else d for d in digits]
    string = ":".join(digits)

    if add_plus:
        string = "+" + string

    return string


def track_standings_to_color(track_data):
    mapping = {0: "gold",
               1: "silver",
               2: "goldenrod"}

    track_standings = get_standings(track_data)[::-1].reset_index()
    track_standings_index = [track_standings[track_standings["Player"] == player].index[0] for player in track_data.index]
    return [mapping[index] if index in mapping.keys() else "white" for index in track_standings_index]


def trackname_to_color(trackname):
    mapping = {"A": "#c1c1c1",
               "B": "#1fa11f",
               "C": "#107df7",
               "D": "#fa2e12",
               "E": "#181818"}

    index = trackname.split("-")[0][0]
    try:
        return mapping[index]
    except KeyError:
        return None




if __name__ == "__main__":
    from calculations import calculate_complete_data
    data = calculate_complete_data()
    plot_total_standings(data)
