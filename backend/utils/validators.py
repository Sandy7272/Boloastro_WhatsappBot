import datetime
import re

def valid_dob(d):
    try:
        dt = datetime.datetime.strptime(d, "%d-%m-%Y")
        return dt < datetime.datetime.now()
    except:
        return False

def valid_time(t):
    return bool(re.match(r"\d{1,2}:\d{2}\s?(AM|PM)", t.upper()))
