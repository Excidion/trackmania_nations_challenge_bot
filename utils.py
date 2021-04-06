import pandas as pd
from datetime import datetime, timedelta
import os
import pymysql
from configparser import ConfigParser
from glob import glob


config = ConfigParser()
config.read("config.ini")



def get_player_name(account_name):
    registrations = get_registration_table()
    try:
        return registrations.loc[account_name, "name"]
    except KeyError:
        return "N/A"

def register_player(account_name, player_name, telegram_id=None):
    registrations = get_registration_table()
    registrations.loc[account_name, "name"] = player_name
    if telegram_id is not None:
        registrations.loc[account_name, "telegram_id"] = telegram_id
    registrations.to_csv(get_registration_table_path())
    print(f"TM-Account \"{account_name}\" has been mapped to \"{player_name}\".")

def get_registration_table():
    try: # already some data saved in the past
        registrations = pd.read_csv(get_registration_table_path())
    except FileNotFoundError: # no data saved in the past
        registrations = pd.DataFrame(columns=["nadeo_account", "name", "telegram_id"])
    finally:
        registrations["telegram_id"].fillna(0, inplace=True)
        registrations["telegram_id"] = registrations["telegram_id"].astype(int)
        return registrations.set_index("nadeo_account")

def get_registration_table_path():
    return os.path.join(
        config.get("LOCAL_STORAGE", "dir"),
        config.get("LOCAL_STORAGE", "registrations"),
    )


def get_last_SQL_update():
    return access_SQL_database("SELECT max(date) FROM `records`")[0][0]


def load_data():
    query = "select c.Id, c.Name, c.Author, p.Login, r.Score, r.Date from records r inner join players p on r.PlayerId=p.Id inner join challenges c on r.ChallengeId=c.Id order by c.Name asc, r.Score asc;"
    rows = list(access_SQL_database(query))
    raw_data = pd.DataFrame(rows, columns=["track_id", "Track", "author", "Player", "Time", "Date"])
    times_table = raw_data[["track_id", "Track", "Date", "Player", "Time", "author"]].copy()
    times_table["Time"] = times_table["Time"].apply(lambda x: timedelta(milliseconds=x))
    times_table["Date"] = times_table["Date"].apply(lambda x: x.to_pydatetime())
    times_table["Origin"] = "Player"
    return times_table


def access_SQL_database(query):
    db = pymysql.connect(
        host = config.get("SQL_LOGIN", "host"),
        port = config.getint("SQL_LOGIN", "port"),
        user = config.get("SQL_LOGIN", "user"),
        passwd = config.get("SQL_LOGIN", "passwd"),
        database = config.get("SQL_LOGIN", "database"),
    )
    cur = db.cursor()
    cur.execute(query)
    result = cur.fetchall()
    db.close()
    return result


def load_medal_times():
    query = "SELECT Id, Name, AuthorTime, GoldTime, SilverTime, BronzeTime from challenges"
    rows = list(access_SQL_database(query))
    data = pd.DataFrame(
        rows,
        columns = [
            "Id",
            "Name",
            "Author",
            "Gold",
            "Silver",
            "Bronze",
        ],
    )
    data.set_index("Id", inplace=True)
    time_cols = ["Author", "Gold", "Silver", "Bronze"]
    data[time_cols] = data[time_cols].applymap(lambda x: timedelta(milliseconds=x))
    return data




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
        register_player(account_name, player_name)
    elif decision == "n":
        print("\nMapping was not saved.")
    else:
        print(f"\nDecision \"{decision}\" invalid.")
        print("Mapping was not saved.")
