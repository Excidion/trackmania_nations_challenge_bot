import pandas as pd
from datetime import datetime, timedelta

def sort_by_track_and_tracks_by_date(data):
    track_min_dates = data.dropna().groupby("Track")["Date"].min()
    track_order = track_min_dates.apply(lambda x: x.isocalendar()[0:2]).sort_values()
    ordered_data = data.set_index("Track").loc[track_order.index].reset_index()
    return ordered_data

def substitute_missing_times(data, medals, remove_non_nadeo=True):
    all_players = data["Player"].unique()

    for track in data["Track"].unique():

        if track not in medals.index.values: # track is not a nadeo track
            if remove_non_nadeo:
                data = data.loc[data["Track"] != track]
            continue

        players_with_time = data.loc[data["Track"] == track, "Player"].unique()
        players_without_time = list(set(all_players) - set(players_with_time))

        if len(players_without_time) == 0: # everybody already has a time
            continue

        slowest_time = data.groupby("Track").max().loc[track, "Time"]
        slower_medals = medals.loc[track].where(medals.loc[track] > slowest_time).dropna()

        if len(slower_medals) == 0: # nobody has beaten any medal time / not all have beaten Bronze
            slower_medals = medals.loc[track].where(medals.loc[track] == medals.loc[track].max()).dropna()

        for player in players_without_time:
            substitute_data = {"Track": track,
                               "Date": None,
                               "Player": player,
                               "Time": slower_medals.min(),
                               "Origin": slower_medals.idxmin()}
            data = data.append(substitute_data, ignore_index=True)

    return data.sort_values("Track").reset_index(drop=True)




def get_individual_records(data):
    return data.groupby("Player").apply(get_track_records).reset_index(drop=True)


def get_track_records(data):
    return data.groupby("Track").min(key="Time").reset_index()


def get_season_standings(data):
    return data.groupby("Player").sum()["Time"].sort_values(ascending=False)
