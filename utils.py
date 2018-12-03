import pandas as pd
from datetime import datetime, timedelta
import os
import pymysql
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

SQL_HOST = config["DATA_SOURCES"]["PLAYER_DATA"]
SQL_USER = config["SQL_LOGIN"]["USER_NAME"]
SQL_PWD = config["SQL_LOGIN"]["PASSWORD"]
SQL_DB = config["SQL_LOGIN"]["DATABASE"]


MEDAL_SOURCE = config["DATA_SOURCES"]["NADEO_MEDALS"]
MEDAL_SP = config["SAVE_POINTS"]["NADEO_MEDALS"]
PN_MAP_SP = config["SAVE_POINTS"]["PLAYER_NAME_MAPPING"]





def get_player_name(account_name):
    account_to_player_map = get_acoount_to_player_map()
    try:
        return account_to_player_map[account_name]
    except KeyError:
        return "N/A"

def set_account_to_player_mapping(account_name, player_name):
    account_to_player_map = get_acoount_to_player_map()
    account_to_player_map.loc[account_name] = player_name
    print(f"TM-Account \"{account_name}\" has been mapped to \"{player_name}\".")
    account_to_player_map.to_pickle(PN_MAP_SP + ".pickle")

    from plots import plot_total_standings
    from main import renew_plot
    renew_plot(load_data()) # redo plots with freshly added names

def get_acoount_to_player_map():
    try: # already some mapping saved in the past
        return pd.read_pickle(PN_MAP_SP + ".pickle")
    except FileNotFoundError: # no player names mapped in the past
        return pd.Series()


def get_last_SQL_update():
    db = pymysql.connect(host = SQL_HOST,
				         user = SQL_USER,
				         passwd = SQL_PWD,
				         database = SQL_DB)
    try:
        cur = db.cursor()
        cur.execute("SELECT max(date) FROM `records`")
        last_update = cur.fetchall()[0][0]
    except Exception as e:
        print(e)

    db.close()
    return last_update



def load_data(location = SQL_HOST):
    is_local_file = os.path.exists(location)

    if is_local_file:
        raw_data = pd.read_csv(location)
    else:
        raw_data = access_SQL_database()

    times_table = raw_data[["Track", "Date", "Player", "Time"]].copy()
    times_table["Time"] = times_table["Time"].apply(lambda x: timedelta(milliseconds=x))

    if is_local_file:
        times_table["Date"] = times_table["Date"].apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
    else:
        times_table["Date"] = times_table["Date"].apply(lambda x: x.to_pydatetime())

    times_table["Origin"] = "Player"
    return times_table


def access_SQL_database():
    db = pymysql.connect(host = SQL_HOST,
				         user = SQL_USER,
				         passwd = SQL_PWD,
				         database = SQL_DB)
    try:
        cur = db.cursor()
        cur.execute("SELECT c.Name, p.Login, r.Score, r.Date FROM records r INNER JOIN players p ON r.PlayerId=p.Id INNER JOIN challenges c ON r.ChallengeId=c.Id ORDER BY c.Name ASC, r.Score ASC;")
        rows = list(cur.fetchall())
        data = pd.DataFrame(rows, columns=['Track','Player','Time','Date'])
    except Exception as e:
        print(e)

    db.close()
    return data





def load_medal_times(location = MEDAL_SOURCE,
                     savepoint_path = MEDAL_SP):

    # check for existing savepoint
    if os.path.exists(savepoint_path + ".pickle"):
        return pd.read_pickle(savepoint_path + ".pickle")


    raw_data = pd.read_html(location, header=0)
    nadeo_medals = pd.DataFrame()
    for table in raw_data:
        try:
            useful_table = table[["Name", "Bronze", "Silver", "Gold", "Author"]]
        except KeyError:
            continue # table does not include all needed columns
        else:
            nadeo_medals = pd.concat([nadeo_medals, useful_table])

    # renameing and reordering
    nadeo_medals.rename({"Name": "Track"}, axis="columns", inplace=True)
    nadeo_medals = nadeo_medals[["Track", "Author", "Gold", "Silver", "Bronze"]]
    nadeo_medals.set_index("Track", inplace=True)

    # finalising & setting savepoint
    nadeo_medals = nadeo_medals.applymap(string_to_timedelta)
    nadeo_medals.to_pickle(savepoint_path + ".pickle")

    return nadeo_medals


def string_to_timedelta(string):
    try:
        time = datetime.strptime(string, "%M'%S\"%f")
    except ValueError: # string contains information about hours
        time = datetime.strptime(string, "%Hh%M'%S\"%f")

    delta = timedelta(hours = time.hour,
                      minutes = time.minute,
                      seconds = time.second,
                      microseconds = time.microsecond)
    return delta




if __name__ == "__main__":
    print("\nThis tool will help you set up the mapping of account names to displayed names.")

    print("What's your name?")
    player_name = input("User: ")

    print("\nWhat's your accout name?")
    account_name = input(player_name + ": ")

    if (player_name == "") or (account_name == ""):
        print("Can not map to/from empty name.\n")
        raise SystemExit

    print(f"\nThe account name \"{account_name}\" will be mapped to player \"{player_name}\". \nDo you wish to continue? (y/n)")
    decision = input(player_name + ": ")
    if decision == "y":
        set_account_to_player_mapping(account_name, player_name)
    elif decision == "n":
        print("\nMapping was not saved.")
    else:
        print(f"\nDecision \"{decision}\" invalid.")
        print("Mapping was not saved.")
