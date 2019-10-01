import pandas as pd
from datetime import datetime, timedelta
import os
import pymysql
import configparser
from glob2 import glob
import re
import pickle

config = configparser.ConfigParser()
config.read("config.ini")

SQL_HOST = config["DATA_SOURCES"]["PLAYER_DATA"]
SQL_USER = config["SQL_LOGIN"]["USER_NAME"]
SQL_PWD = config["SQL_LOGIN"]["PASSWORD"]
SQL_DB = config["SQL_LOGIN"]["DATABASE"]


NADEO_MEDAL_SOURCE = config["DATA_SOURCES"]["NADEO_MEDALS"]
NADEO_MEDAL_SP = config["SAVE_POINTS"]["NADEO_MEDALS"]

CUSTOM_MEDAL_SOURCE = config["DATA_SOURCES"]["TM_SERVER_MAP_DIR"]
CUSTOM_MEDAL_SP = config["SAVE_POINTS"]["CUSTOM_MEDALS"]

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
    account_to_player_map.to_pickle(PN_MAP_SP + ".pickle")
    print(f"TM-Account \"{account_name}\" has been mapped to \"{player_name}\".")


def get_acoount_to_player_map():
    try: # already some mapping saved in the past
        return pd.read_pickle(PN_MAP_SP + ".pickle")
    except FileNotFoundError: # no player names mapped in the past
        return pd.Series()


def get_last_SQL_update():
    return access_SQL_database("SELECT max(date) FROM `records`")[0][0]


def load_data(location = SQL_HOST):
    is_local_file = os.path.exists(location)

    if is_local_file:
        raw_data = pd.read_csv(location)
    else:
        raw_data = download_data()

    times_table = raw_data[["Track", "Date", "Player", "Time"]].copy()
    times_table["Time"] = times_table["Time"].apply(lambda x: timedelta(milliseconds=x))

    if is_local_file:
        times_table["Date"] = times_table["Date"].apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
    else:
        times_table["Date"] = times_table["Date"].apply(lambda x: x.to_pydatetime())

    times_table["Origin"] = "Player"
    return times_table


def download_data():
    query = "SELECT c.Id as Id
		, c.Uid as Uid
		, c.Name as TrackName
		, c.Author as TrackAuthor
		, c.BronzeTime as TrackBronzeTime
		, c.SilverTime as TrackSilverTime
		, c.GoldTime as TrackGoldTime
		, c.AuthorTime as TrackAuthorTime
		, p.Login as PlayerLogin
		, r.Score as Score
		, r.Date as Date
		FROM records r 
		INNER JOIN players p 
		ON r.PlayerId=p.Id 
		INNER JOIN challenges c 
		ON r.ChallengeId=c.Id 
		ORDER BY c.Name ASC
		, r.Score ASC;"
    rows = list(access_SQL_database(query))
    return pd.DataFrame(rows, columns=['Id'
				       ,'Uid'
				       ,'Track'
				       ,'TrackAuthor'
				       ,'TrackBronzeTime'
				       ,'TrackSilverTime'
				       ,'TrackGoldTime'
				       ,'TrackAuthorTime'
				       ,'Player'
				       ,'Time'
				       ,'Date'])


def access_SQL_database(query):
    db = pymysql.connect(host = SQL_HOST,
				         user = SQL_USER,
				         passwd = SQL_PWD,
				         database = SQL_DB)
    cur = db.cursor()
    cur.execute(query)
    result = cur.fetchall()
    db.close()
    return result




def load_medal_times():
    nadeo_medals = load_nadeo_medals()
    custom_medals = load_custom_medals()
    return pd.concat([nadeo_medals, custom_medals])


def load_nadeo_medals(location=NADEO_MEDAL_SOURCE, savepoint_path=NADEO_MEDAL_SP):
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


def load_custom_medals(location=CUSTOM_MEDAL_SOURCE, savepoint_path=CUSTOM_MEDAL_SP):
    custom_mapfiles = glob(f"{location}*.Gbx")
    custom_mapfiles.sort() # list of already read maps has to be in consisten order

    # check if all maps in mapfolder have already been read to databse
    if os.path.exists(f"{savepoint_path}.p"):
        with open(f"{savepoint_path}.p", "rb") as file:
            if custom_mapfiles == pickle.load(file):
                if os.path.exists(savepoint_path + ".pickle"): # check for existing savepoint
                    return pd.read_pickle(savepoint_path + ".pickle")


    custom_medals = pd.DataFrame(columns=["Track", "Author", "Gold", "Silver", "Bronze"])

    for mapfile in custom_mapfiles:
        with open(mapfile,"r",errors="ignore") as file:
            content = file.read()
        mapinfo = read_mapinfo(content)
        custom_medals = custom_medals.append({"Track":  mapinfo["name"],
                                              "Author": mapinfo["authortime"],
                                              "Gold":   mapinfo["gold"],
                                              "Silver": mapinfo["silver"],
                                              "Bronze": mapinfo["bronze"]},
                                             ignore_index=True)
    custom_medals.set_index("Track", inplace=True)

    # setting savepoint
    custom_medals.to_pickle(savepoint_path + ".pickle")
    with open(f"{savepoint_path}.p", "wb") as file:
        pickle.dump(custom_mapfiles, file)

    return custom_medals


def read_mapinfo(content):
    regex_name = re.compile("name=\"")
    regex_author = re.compile("\" author=")
    regex_times = re.compile("<times ")
    regex_authorscore = re.compile(" authorscore=")

    result = {"name": regex_author.split(regex_name.split(content)[1])[0]}
    times = regex_authorscore.split(regex_times.split(content)[1])[0]
    for time in times.split():
        medal, score = time.split("=")
        score = timedelta(milliseconds=int(score.replace("\"","")))
        result[medal] = score
    return result




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
