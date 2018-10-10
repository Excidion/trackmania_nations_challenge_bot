import pandas as pd
from datetime import datetime, timedelta
from matplotlib import pyplot as plt

from calculations import get_season_standings


def timedelta_to_string(td, add_plus=False):
    if not isinstance(td, timedelta):
        return ""

    hours = int(td.seconds//3600)
    minutes = int(td.seconds//60%60)
    seconds = int(td.seconds-hours*3600-minutes*60)
    milliseconds = int(td.microseconds/10**4)

    if hours > 0:
        string =  f"{hours}:{minutes}:{seconds}.{milliseconds}"
    elif minutes > 0:
        string =  f"{minutes}:{seconds}.{milliseconds}"
    else:
        string =  f"{seconds}.{milliseconds}"

    digits = string.split(":")
    digits = ["0" + d if len(d.split(".")[0])==1 else d for d in digits]
    string = ":".join(digits)

    if add_plus:
        string = "+" + string

    return string


def trackname_to_color(trackname):
    mapping = {"A": "#c1c1c1",
               "B": "#1fa11f",
               "C": "#107df7",
               "D": "#fa2e12",
               "E": "#181818"}

    index = trackname.split("-")[0][0]
    try:
        return mapping[index]
    except KeyError:
        return None
