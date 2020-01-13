import pandas as pd
from datetime import datetime, timedelta
from utils import load_data, load_medal_times




def calculate_complete_data():
    raw_data = load_data()
    medals = load_medal_times()
    individual_records = get_individual_records(raw_data)
    data = substitute_missing_times(individual_records, medals)
    data = sort_by_track_and_tracks_by_date(data)
    data.groupby("Player")["Time"].sum()
    return data


def sort_by_track_and_tracks_by_date(data):
    track_min_dates = data.dropna().groupby("track_id")["Date"].min()
    track_order = track_min_dates.apply(lambda x: x.isocalendar()[0:2]).sort_values()
    ordered_data = data.set_index("track_id").loc[track_order.index].reset_index()
    return ordered_data

def substitute_missing_times(data, medals, remove_unknown=True):
    all_players = data["Player"].unique()
    track_id_map = data.set_index("track_id")["Track"].drop_duplicates()

    for track, track_data in data.groupby("track_id"):
        if track not in medals.index.values: # track's medals not in database
            if remove_unknown:
                data = data.loc[data["track_id"] != track]
            continue

        players_with_time = track_data["Player"].unique()
        players_without_time = list(set(all_players) - set(players_with_time))
        if len(players_without_time) == 0: # everybody already has a time
            continue

        slowest_time = track_data["Time"].max()
        cols = ["Author", "Gold", "Silver", "Bronze"]
        slower_medals = medals.loc[track, cols].where(medals.loc[track, cols] > slowest_time).dropna()
        if len(slower_medals) == 0: # nobody has beaten any medal time / not all have beaten Bronze
            substitute_time = medals.loc[track, "Bronze"]
        else: # this should be the regular case
            substitute_time = slower_medals.min()

        for player in players_without_time:
            substitute_data = {
                "track_id": track,
                "Track": track_id_map.loc[track],
                "Date": None,
                "Player": player,
                "Time": substitute_time,
                "Origin": slower_medals[slower_medals == slower_medals.min()].index[0],
            }
            data = data.append(substitute_data, ignore_index=True)

    return data.sort_values("track_id").reset_index(drop=True)


def get_current_track_data(data):
    current_track = data.loc[data["Date"] == data["Date"].dropna().max(), "track_id"].values[0]
    return data[data["track_id"] == current_track].copy()

def get_individual_records(data):
    return data.groupby("Player").apply(get_track_records).reset_index(drop=True)


def get_track_records(data):
    return data.groupby("track_id").min(key="Time").reset_index()


def get_standings(data):
    return data.groupby("Player")["Time"].sum().sort_values(ascending=False)
