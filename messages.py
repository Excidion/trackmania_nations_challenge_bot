from calculations import get_standings, calculate_complete_data, get_current_track_data
from utils import get_player_name
from plots import timedelta_to_string


def info_about_current_weeks_ladder_changes(old_data, new_data):
    messages = []

    new_data = get_current_track_data(new_data)
    new_data = new_data[new_data["Origin"] == "Player"]
    new_ladder = get_standings(new_data)

    current_track = new_data["Track"].unique()[0]

    old_data = old_data[old_data["Track"] == current_track]
    old_data = old_data[old_data["Origin"] == "Player"]
    old_ladder = get_standings(old_data)

    try:
        changes = new_ladder.index != old_ladder.index
    except ValueError: # a new player/track is in the database.
        player_overlap = list(set(new_ladder.index) | set(old_ladder.index))
        new_ladder = new_ladder.loc[new_ladder.index.isin(player_overlap)]
        old_ladder = old_ladder.loc[old_ladder.index.isin(player_overlap)]
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
        message = f"{track}: {get_player_name(player_name)} scored a new record of {new_record}!"
        messages.append(message)

    return messages

def get_ladder_as_html():
    data = get_current_track_data(calculate_complete_data())
    data = data[data["Origin"] == "Player"]
    ladder = get_standings(data)

    message_lines = [data["Track"].unique()[0]]
    for i, player in enumerate(list(reversed(ladder.index))):
        line = f"{i+1}) "
        line += get_player_name(player) + ": "
        line += timedelta_to_string(ladder[player]) + " "
        message_lines.append(line)

    max_linelength = max([len(line) for line in message_lines])
    missing_spaces = [(max_linelength-len(line)) for line in message_lines]
    message_lines = [(":"+spaces*" ").join(line.split(":")) for spaces, line in zip(missing_spaces, message_lines)]

    message = "\n".join(message_lines)
    return f"<pre>{message}</pre>"
