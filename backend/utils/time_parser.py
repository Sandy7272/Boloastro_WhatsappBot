import re
from datetime import datetime

def parse_time(t):

    t=t.lower().replace(" ","")

    formats=["%I.%M%p","%I:%M%p","%H:%M"]

    for f in formats:
        try:
            return datetime.strptime(t,f).strftime("%H:%M")
        except:
            pass

    return None
