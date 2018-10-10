import configparser
from utils import load_data, load_medal_times
from calculations import get_individual_records, substitute_missing_times, sort_by_track_and_tracks_by_date, get_season_standings

from calculations import  *
from plots import *
import pandas as pd
from datetime import datetime, timedelta
from matplotlib import pyplot as plt

import matplotlib.dates as mdates
import numpy as np


if __name__ == "__main__":

    config = configparser.ConfigParser()
    config.read("config.ini")

    raw_data = load_data(config["DATA_SOURCES"]["PLAYER_DATA"])
    nadeo_medals = load_medal_times(config["DATA_SOURCES"]["NADEO_MEDALS"])

    individual_records = get_individual_records(raw_data)
    data = substitute_missing_times(individual_records, nadeo_medals)

    data = sort_by_track_and_tracks_by_date(data)

    data


if True:

    fig, ax = plt.subplots()

    season_standings = get_season_standings(data)

    # preparing for mutiple bar alignment
    bar_alignment = pd.Series({p:timedelta(0) for p in season_standings.index}, name="Time")

    for track in data["Track"].unique():

        # subset for track, ordered by total times
        track_data = data.loc[data["Track"] == track]
        track_data = track_data.set_index("Player").loc[season_standings.index]


        # colored barplots for each player & track
        bars = ax.barh(y = track_data.index,
                       width = track_data["Time"],
                       #left = bar_alignment,
                       color = trackname_to_color(track),
                       edgecolor = "white")



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
    year, week = data.dropna()["Date"].max().isocalendar()[0:2]
    fig.savefig(f"Meisterschaftsstand_y{year}_w{week}.pdf", bbox_inches = "tight")
