import pandas as pd
from datetime import datetime, timedelta
import os
import mysql.connector
import configparser

config = configparser.ConfigParser()
config.read("config.ini")




def get_last_SQL_update():
    db = mysql.connector.connect(host = config["DATA_SOURCES"]["PLAYER_DATA"],
				                 user = config["SQL_LOGIN"]["USER_NAME"],
				                 passwd = config["SQL_LOGIN"]["PASSWORD"],
				                 database = config["SQL_LOGIN"]["DATABASE"])

    cur = db.cursor()
    cur.execute("SELECT max(date) FROM `records`")
    return cur.fetchall()[0][0]



def load_data(location = config["DATA_SOURCES"]["PLAYER_DATA"]):
    if os.path.exists(location):
        raw_data = pd.read_csv(location)
    else:
        raw_data = access_SQL_database()

    times_table = raw_data[["Track", "Date", "Player", "Time"]].copy()
    times_table["Time"] = times_table["Time"].apply(lambda x: timedelta(milliseconds=x))

    try: # when source is csv file
        times_table["Date"] = times_table["Date"].apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
    except TypeError: # when source is sql directly
        times_table["Date"] = times_table["Date"].apply(lambda x: x.to_pydatetime())

    times_table["Origin"] = "Player"
    return times_table


def access_SQL_database():
	db = mysql.connector.connect(host = config["DATA_SOURCES"]["PLAYER_DATA"],
				                 user = config["SQL_LOGIN"]["USER_NAME"],
				                 passwd = config["SQL_LOGIN"]["PASSWORD"],
				                 database = config["SQL_LOGIN"]["DATABASE"])

	cur = db.cursor()
	cur.execute("SELECT c.Name, p.NickName, r.Score, r.Date FROM records r INNER JOIN players p ON r.PlayerId=p.Id INNER JOIN challenges c ON r.ChallengeId=c.Id ORDER BY c.Name ASC, r.Score ASC;")

	rows = list(cur.fetchall())
	columnlist = ['Track','Player','Time','Date']

	return pd.DataFrame(rows, columns=columnlist)




def load_medal_times(location = config["DATA_SOURCES"]["NADEO_MEDALS"],
                     savepoint_path = config["SAVE_POINTS"]["NADEO_MEDALS"]):

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
