import datetime

from .format import format_dt


def format_relative(dt: datetime.datetime) -> str:
    return format_dt(dt, "R")
