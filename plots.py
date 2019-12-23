import matplotlib
matplotlib.use("Agg") # fix for running on machine without display
import matplotlib.ticker as ticker
import pandas as pd
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
from configparser import ConfigParser
import os

from calculations import get_standings
from utils import get_player_name

import warnings
warnings.filterwarnings("ignore", category=UserWarning) # warning with tight layout


config = ConfigParser()
config.read("config.ini")




def plot_total_standings(data, to_file=True, backup_name=None):
    width = data["track_id"].nunique() + 3
    height = data["Player"].nunique()
    fig, ax = plt.subplots(figsize=(width, height))

    season_standings = get_standings(data)

    # preparing for mutiple bar alignment
    bar_alignment = pd.Series({p:timedelta(0) for p in season_standings.index}, name="Time")

    for track, track_data in data.groupby("track_id", sort=False):
        # order subset by total times
        track_data = track_data.set_index("Player").loc[season_standings.index]
        trackname = track_data["Track"].iloc[0]
        nadeo = track_data["author"].iloc[0] == "Nadeo"

        # colored barplots for each player & track
        bars = ax.barh(y = track_data.index,
                       width = track_data["Time"].apply(timedelta.total_seconds),
                       left = bar_alignment.apply(timedelta.total_seconds),
                       color = trackname_to_color(trackname, nadeo),
                       edgecolor = fig.patch.get_facecolor())

        # adding up times of plotted track times for following bar plots alignment
        bar_alignment += track_data["Time"]


        # labeling bars with time information
        for i, bar in enumerate(bars):
            if track_data["Origin"][i] == "Player":
                label = timedelta_to_string(track_data["Time"][i])
            else: # no time was set by player
                label = track_data["Origin"][i] # label with medal name

            # label each bar
            ax.text(y = bar.get_y() + bar.get_height()/2,
                    x = bar.get_x() + bar.get_width()/2 ,
                    s = label,
                    horizontalalignment = "center",
                    verticalalignment = "center",
                    color = fig.patch.get_facecolor())


        # labeling groups of bars with track names
        ax.text(y = bar.get_y() + bar.get_height()*1.5,
                x = bar.get_x() + bar.get_width()/2,
                s = trackname.split("-")[0] if nadeo else trackname,
                color = trackname_to_color(trackname, nadeo),
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


    # axis decorating
    plt.yticks(track_data.index, track_data.index.map(get_player_name))
    ax.set_xlabel("Total Time")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    max_time = season_standings.max().total_seconds()
    if max_time > 2*60:
        major_ticks = 60
        minor_ticks = 15
    elif max_time > 60:
        major_ticks = 30
        minor_ticks = 10
    elif max_time > 30:
        major_ticks = 15
        minor_ticks = 5
    else:
        major_ticks = 10
        minor_ticks = 1

    ax.xaxis.set_major_locator(ticker.MultipleLocator(major_ticks))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(minor_ticks))
    ax.xaxis.set_major_formatter(timedelta_formatter)
    fig.tight_layout()


    # save & close
    if not backup_name == None:
        fig.savefig(
            os.path.join(config.get("LOCAL_STORAGE", "dir"), f"{backup_name}.pdf"),
            bbox_inches = "tight",
    )
    if to_file:
        fig.savefig(
            os.path.join(
                config.get("LOCAL_STORAGE", "dir"),
                config.get("LOCAL_STORAGE", "total_standings")
            ),
            dpi = 225,
            transparent = True,
            bbox_inches = "tight",
            pad_inches = 0,
        )
        plt.close(fig)
    else:
        return plt.gca()


@ticker.FuncFormatter
def timedelta_formatter(x, pos):
    string = timedelta_to_string(timedelta(seconds=x)).split(".")[0]
    if len(string) == 2:
        string = f"00:{string}"
    return string


def timedelta_to_string(td, add_plus=False):
    if not isinstance(td, timedelta):
        return ""

    hours = int(td.seconds//3600)
    minutes = int(td.seconds//60%60)
    seconds = int(td.seconds-hours*3600-minutes*60)
    centiseconds = int(td.microseconds/10**4)

    if hours > 0:
        string =  f"{hours}:{minutes}:{seconds}.{centiseconds}"
    elif minutes > 0:
        string =  f"{minutes}:{seconds}.{centiseconds}"
    else:
        string =  f"{seconds}.{centiseconds}"

    digits = string.split(":")
    digits = ["0" + d if len(d.split(".")[0])==1 else d for d in digits]
    string = ":".join(digits)

    pre, centi = string.split(".")
    if len(centi) == 1:
        centi = "0" + centi
    string = f"{pre}.{centi}"

    if add_plus:
        string = "+" + string

    return string


def track_standings_to_color(track_data):
    mapping = {
        0: "gold",
        1: "silver",
        2: "goldenrod",
    }
    track_standings = get_standings(track_data)[::-1].reset_index()
    track_standings_index = [track_standings[track_standings["Player"] == player].index[0] for player in track_data.index]
    return [mapping[index] if index in mapping.keys() else "white" for index in track_standings_index]


def trackname_to_color(trackname="", nadeo=True):
    mapping = {
        "A": "#c1c1c1",
        "B": "#1fa11f",
        "C": "#107df7",
        "D": "#fa2e12",
        "E": "#181818",
    }
    if nadeo:
        try:
            return mapping[trackname[0]]
        except KeyError or IndexError: pass
    return "orange"




if __name__ == "__main__":
    from calculations import calculate_complete_data
    data = calculate_complete_data()
    plot_total_standings(data)
