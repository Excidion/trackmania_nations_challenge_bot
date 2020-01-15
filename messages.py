from calculations import get_standings, get_current_track_data
from utils import get_player_name
from plots import timedelta_to_string


def info_about_current_weeks_ladder_changes(old_data, new_data):
    new_data = get_current_track_data(new_data)
    new_data = new_data[new_data["Origin"] == "Player"]
    new_ladder = get_standings(new_data)
    current_track = new_data["track_id"].unique()[0]
    old_data = old_data[old_data["track_id"] == current_track]
    old_data = old_data[old_data["Origin"] == "Player"]
    old_ladder = get_standings(old_data)

    player_overlap = list(set(new_ladder.index) & set(old_ladder.index))
    new_ladder = new_ladder.loc[new_ladder.index.isin(player_overlap)]
    old_ladder = old_ladder.loc[old_ladder.index.isin(player_overlap)]
    changes = new_ladder.index != old_ladder.index
    new_ladder = new_ladder[changes].reset_index().reset_index().set_index("Player")
    old_ladder = old_ladder[changes].reset_index().reset_index().set_index("Player")
    new_ladder["index_change"] = new_ladder["index"] - old_ladder["index"]

    messages = []
    for player in new_ladder.index.values:
        overtakes = new_ladder.loc[player, "index_change"]
        if not overtakes > 0:
            continue
        index = new_ladder.loc[player, "index"]
        overtook = new_ladder[(new_ladder["index"] >= index-overtakes) & (new_ladder["index"] < index)].index.values
        have_scored = old_data.loc[old_data["Origin"] == "Player", "Player"].unique()
        overtook = ", ".join([get_player_name(p) for p in overtook if p in have_scored])
        new_record = new_data.groupby(["Player", "track_id"])["Time"].min().loc[player, current_track]
        messages.append(
            f"{get_player_name(player)} scored a {timedelta_to_string(new_record)} and overtook {overtook}."
        )
    return messages


def info_about_new_times(old_data, new_data):
    messages = []
    new_entries_index = new_data[~new_data.isin(old_data)].dropna(how="all").index
    new_entries = new_data.loc[new_entries_index]
    for row_index, entry in new_entries.iterrows():
        player_name = entry["Player"]
        new_record = timedelta_to_string(entry["Time"])
        track = entry["Track"]
        message = f"{track}: {get_player_name(player_name)} scored a new record of {new_record}!"
        messages.append(message)
    return messages
