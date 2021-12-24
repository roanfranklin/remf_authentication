import sqlite3

def initial_sqlite(_DIR):
    DB = '{0}/data/database.sqlite3'.format(_DIR)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
CREATE TABLE IF NOT EXISTS rpcsaved (
id INTEGER PRIMARY KEY AUTOINCREMENT,
myorder INTEGER DEFAULT 1,
issuer TEXT DEFAULT '',
account TEXT DEFAULT '',
secret TEXT DEFAULT '',
basekey TEXT DEFAULT 'totp'
);
    """)
    conn.commit()
    conn.close()

def sqlite_query(_DIR, SQL_QUERY):
    DB = '{0}/data/database.sqlite3'.format(_DIR)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(SQL_QUERY)
    data = cur.fetchall()
    conn.close()
    return data

def db_selectoneRPC(_DIR, _ID):
    DB = '{0}/data/database.sqlite3'.format(_DIR)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM auth WHERE id = {0}".format(_ID))
    data = cur.fetchone()
    conn.close()
    return dict(data)

def db_insertRPC(_DIR, RPC_DATA):
    DB = '{0}/data/database.sqlite3'.format(_DIR)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("INSERT INTO auth (issuer, account, secret, basekey, status) VALUES (:issuer, :account, :secret, :basekey, :status)", RPC_DATA)
    if cur.rowcount < 1:
        status = False
    else:
        status = True
    conn.commit()
    __data = None
    if status:
        cur.execute("SELECT last_insert_rowid() -- same as select @@identity")
        __data = cur.fetchone()
        conn.commit()

        cur.execute("UPDATE auth SET myorder = {0} WHERE id = {0}".format(__data[0]))
        conn.commit()

        cur.execute("SELECT * FROM auth WHERE id = {0}".format(__data[0]))
        data = cur.fetchone()
        if cur.rowcount < 1:
            status = False
        else:
            status = True
    conn.close()

    return data, status

def db_removeRPC(_DIR, RPC_DATA):
    DB = '{0}/data/database.sqlite3'.format(_DIR)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"DELETE FROM auth WHERE id = :id", RPC_DATA)
    if cur.rowcount < 1:
        status = False
    else:
        status = True
    conn.commit()
    conn.close()
    return status

def updown_data(_DIR, data_dict):
    DB = '{0}/data/database.sqlite3'.format(_DIR)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("UPDATE {0} SET myorder = :myordernew WHERE id = :idold".format(data_dict['table']), data_dict)
    if cur.rowcount < 1:
        status = False
    else:
        status = True
    conn.commit()
    cur.execute("UPDATE {0} SET myorder = :myorderold WHERE id = :idnew".format(data_dict['table']), data_dict)
    if cur.rowcount < 1:
        status = False
    else:
        status = True
    conn.commit()
    conn.close()

    return status