# https://charlesleifer.com/blog/encrypted-sqlite-databases-with-python-and-sqlcipher/
# https://www.zetetic.net/sqlcipher/sqlcipher-api/
#
# try:
#     from sqlcipher3 import dbapi2 as sqlite3
# except:
#     import sqlite3

from sqlcipher3 import dbapi2 as sqlite3

def teste_connection(__APP_DATA):
    try:
        conn = sqlite3.connect(__APP_DATA['file'])
        conn.row_factory = sqlite3.Row
        conn.execute('pragma key="{0}"'.format(__APP_DATA['secret']))
        result = conn.execute('SELECT * FROM auth;').fetchall()
        return result
    except:
        return None

def initial_sqlite(__APP_DATA):
    conn = sqlite3.connect(__APP_DATA['file'])
    conn.row_factory = sqlite3.Row
    conn.execute("ATTACH DATABASE '{0}' AS encrypted KEY '{1}';".format(__APP_DATA['file'], __APP_DATA['secret']))  # setando senha = linha 1
    conn.execute("SELECT sqlcipher_export('encrypted');")                                                      # setando senha = linha 2
    conn.execute("DETACH DATABASE encrypted;")                                                                 # setando senha = linha 3
    conn.execute('pragma key="{0}"'.format(__APP_DATA['secret']))                                              # Acesso aos SELECT, INSERT, UPDATE e DELETE
    cur = conn.cursor()
    cur.execute("""
CREATE TABLE IF NOT EXISTS auth (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    myorder INTEGER DEFAULT 1,
    basekey TEXT    DEFAULT totp,
    issuer  TEXT    NOT NULL,
    account TEXT    NOT NULL,
    secret  TEXT    NOT NULL,
    status  INTEGER DEFAULT (1) 
);
    """)
    conn.commit()    
    conn.close()

def sqlite_query(__APP_DATA, SQL_QUERY):
    conn = sqlite3.connect(__APP_DATA['file'])
    conn.row_factory = sqlite3.Row
    conn.execute('pragma key="{0}"'.format(__APP_DATA['secret']))
    cur = conn.cursor()
    cur.execute(SQL_QUERY)
    data = cur.fetchall()
    conn.close()
    return data

def db_selectoneRPC(__APP_DATA, _ID):
    conn = sqlite3.connect(__APP_DATA['file'])
    conn.row_factory = sqlite3.Row    
    conn.execute('pragma key="{0}"'.format(__APP_DATA['secret']))
    cur = conn.cursor()
    cur.execute("SELECT * FROM auth WHERE id = {0}".format(_ID))
    data = cur.fetchone()
    conn.close()
    return dict(data)

def db_insertRPC(__APP_DATA, RPC_DATA):
    conn = sqlite3.connect(__APP_DATA['file'])
    conn.row_factory = sqlite3.Row
    conn.execute('pragma key="{0}"'.format(__APP_DATA['secret']))
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

def db_removeRPC(__APP_DATA, RPC_DATA):
    conn = sqlite3.connect(__APP_DATA['file'])
    conn.row_factory = sqlite3.Row    
    conn.execute('pragma key="{0}"'.format(__APP_DATA['secret']))
    cur = conn.cursor()
    cur.execute(f"DELETE FROM auth WHERE id = :id", RPC_DATA)
    if cur.rowcount < 1:
        status = False
    else:
        status = True
    conn.commit()
    conn.close()
    return status

def updown_data(__APP_DATA, data_dict):
    conn = sqlite3.connect(__APP_DATA['file'])
    conn.row_factory = sqlite3.Row    
    conn.execute('pragma key="{0}"'.format(__APP_DATA['secret']))
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