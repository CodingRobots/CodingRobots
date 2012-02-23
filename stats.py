import sqlite3
import os
import hashlib
import conf


dbversion = 2


def dbopen():
    global conn
    conn = sqlite3.connect(conf.dbfile)
    conn.row_factory = sqlite3.Row
    global c
    c = conn.cursor()

def dbclose():
    conn.close()

def dbcheck():
    if not os.path.exists(conf.dbfile):
        initialize()
        print 'stats database initialized'

    if not dbcheckver():
        print 'ERROR: Database version mismatch.'
        return False
    else:
        return True

def dbcheckver():
    dbopen()
    q = '''SELECT count(*)
            FROM sqlite_master
            WHERE type='table' AND
                name='dbversion'
        '''
    c.execute(q)
    r = c.fetchone()
    if not r[0]:
        # No dbversion table exists
        retval = 0
    else:
        q = '''SELECT n
                FROM dbversion'''
        c.execute(q)
        r = c.fetchone()
        ver = r[0]
        retval = ver == dbversion

    dbclose()
    return retval

def dbremove():
    if os.path.exists(conf.dbfile):
        os.remove(conf.dbfile)

def initialize():
    'Create empty database'

    schemadef = '''\

CREATE TABLE dbversion (
    n integer
);

CREATE TABLE stats (
    program_name text,
    fingerprint text,
    matches integer,
    wins integer,
    opponents integer,
    kills integer,
    damage_caused integer
);

CREATE TABLE tournament_stats (
    tournament datetime,
    program_name text,
    fingerprint text,
    matches integer,
    wins integer,
    opponents integer,
    kills integer,
    damage_caused integer
);

    '''

    dbopen()
    conn.executescript(schemadef)
    conn.commit()

    q = '''INSERT INTO dbversion
            VALUES (:n)
    '''
    n = dbversion
    c.execute(q, locals())
    conn.commit()

    dbclose()



def fingerprint(name):
    fname = '%s.py' % name
    for d in conf.robot_dirs:
        pth = os.path.join(d, fname)
        if os.path.exists(pth):
            break

    m = hashlib.md5()
    for line in file(pth):
        m.update(line)

    return m.hexdigest()

def exists(name, fp):
    q = '''\
    SELECT *
    FROM stats
    WHERE program_name=:name AND
            fingerprint=:fp
    '''
    c.execute(q, locals())
    r = c.fetchall()
    return bool(r)

def update(name, win, opponents, kills, damage_caused):
    fp = fingerprint(name)
    win = int(win) # turn True/False in to 1/0
    if exists(name, fp):
        q = '''\
        UPDATE stats
        SET matches = matches + 1,
            wins = wins + :win,
            opponents = opponents + :opponents,
            kills = kills + :kills,
            damage_caused = damage_caused + :damage_caused
        WHERE
            program_name = :name AND
            fingerprint = :fp
        '''

    else:
        q = '''\
        INSERT INTO stats
            (program_name,
                fingerprint,
                matches,
                wins,
                opponents,
                kills,
                damage_caused)
            VALUES
                (:name,
                    :fp,
                    1,
                    :win,
                    :opponents,
                    :kills,
                    :damage_caused)
        '''
    c.execute(q, locals())
    conn.commit()



def tournament_exists(tournament, name, fp):
    q = '''\
    SELECT *
    FROM tournament_stats
    WHERE tournament = :tournament AND
            program_name = :name AND
            fingerprint = :fp
    '''
    c.execute(q, locals())
    r = c.fetchall()
    return bool(r)

def tournament_update(tournament, kind, name, win, opponents, kills, damage_caused):
    fp = fingerprint(kind)
    win = int(win) # turn True/False in to 1/0
    if tournament_exists(tournament, name, fp):
        q = '''\
        UPDATE tournament_stats
        SET matches = matches + 1,
            wins = wins + :win,
            opponents = opponents + :opponents,
            kills = kills + :kills,
            damage_caused = damage_caused + :damage_caused
        WHERE
            tournament = :tournament AND
            program_name = :name AND
            fingerprint = :fp
        '''

    else:
        q = '''\
        INSERT INTO tournament_stats
            (tournament,
                program_name,
                fingerprint,
                matches,
                wins,
                opponents,
                kills,
                damage_caused)
            VALUES
                (:tournament,
                    :name,
                    :fp,
                    1,
                    :win,
                    :opponents,
                    :kills,
                    :damage_caused)
        '''
    c.execute(q, locals())
    conn.commit()

def tournament_results(tournament):
    q = '''
    SELECT *
    FROM tournament_stats
    WHERE tournament = :tournament
    ORDER BY
        wins DESC,
        kills DESC

    '''

    c.execute(q, locals())
    r = c.fetchall()
    return r
