import matplotlib
matplotlib.use("Agg")
import pandas as pd
from datetime import datetime, timedelta
from matplotlib import pyplot as plt

from calculations import get_standings

import configparser
config = configparser.ConfigParser()
config.read("config.ini")


def plot_total_standings(data, filename):
        fig, ax = plt.subplots()

        season_standings = get_standings(data)

        # preparing for mutiple bar alignment
        bar_alignment = pd.Series({p:timedelta(0) for p in season_standings.index}, name="Time")

        for track in data["Track"].unique():

            # subset for track, ordered by total times
            track_data = data.loc[data["Track"] == track]
            track_data = track_data.set_index("Player").loc[season_standings.index]


            # colored barplots for each player & track
            bars = ax.barh(y = track_data.index,
                           width = track_data["Time"].apply(timedelta.total_seconds),
                           left = bar_alignment.apply(timedelta.total_seconds),
                           color = trackname_to_color(track),
                           edgecolor = "white")#track_standings_to_color(track_data))



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
        ax.set_xlabel("Total Time")
        #ax.xaxis_date()
        #myFmt = mdates.DateFormatter("%M:%S")
        #ax.xaxis.set_major_formatter(myFmt)
        #ax.set_xlim(timedelta(0), season_standings.max() + timedelta(seconds = 30))

        # save
        fig.tight_layout()
        plot_dir = config["SAVE_POINTS"]["PLOT_DIR"]
        current_plot_name = config["SAVE_POINTS"]["CURRENT_PLOT"]
        fig.savefig(f"{plot_dir}/{filename}.pdf", bbox_inches = "tight")
        fig.savefig(f"{plot_dir}/{current_plot_name}.pdf", bbox_inches = "tight")




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
