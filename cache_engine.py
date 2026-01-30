import hashlib,json
from db_engine import get_conn

def get_hash(phone,d):
    s=f"{phone}{d['dob']}{d['time']}{d['place']}"
    return hashlib.md5(s.encode()).hexdigest()

def get_cached(h):
    conn=get_conn();cur=conn.cursor()
    cur.execute("SELECT payload FROM kundali_cache WHERE hash=%s",(h,))
    r=cur.fetchone();conn.close()
    return r[0] if r else None

def save_cache(h,payload):
    conn=get_conn();cur=conn.cursor()
    cur.execute("INSERT INTO kundali_cache VALUES(%s,%s)",(h,json.dumps(payload)))
    conn.commit();conn.close()
