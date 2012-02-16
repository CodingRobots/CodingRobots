import sqlite3
import os
import hashlib
import conf
import util


dbversion = 3
dbversion_reset = dbversion


def fullpath():
    rdirs = util.get_robot_dirs()

    if conf.dbfile.startswith('~'):
        fname = os.path.expanduser(conf.dbfile)
    elif not rdirs:
        fname = conf.dbfile
    else:
        fdir = rdirs[0]
        fname = os.path.join(fdir, conf.dbfile)

    fname = os.path.abspath(fname)
    head, tail = os.path.split(fname)
    if not os.path.exists(head):
        fname = '/:::NONEXISTANT:::'

    return fname


def dbopen():
    global dbversion
    if dbversion == ':memory:':
        return

    global conn
    fname = fullpath()

    if not os.path.exists(fname):
        newdb = True
    else:
        newdb = False

    try:
        conn = sqlite3.connect(fname)
        if newdb:
            print 'New stats database file started'
    except sqlite3.OperationalError:
        print 'Cannot open database file. Working in :memory:'
        conn = sqlite3.connect(':memory:')
        dbversion = ':memory:'

    conn.row_factory = sqlite3.Row
    global c
    c = conn.cursor()

    if dbversion == ':memory:' or newdb:
        initialize()


def dbclose(restart=False):
    global dbversion
    if restart or dbversion != ':memory:':
        conn.close()
    if restart:
        dbversion = dbversion_reset

def trywrite():
    dbopen()
    q = '''
    UPDATE trywrite SET tw=1;
    '''
    try:
        c.execute(q)
    except (sqlite3.OperationalError, sqlite3.ProgrammingError):
        return False

    return True

def dbcheck():
    fname = fullpath()
    print 'Checking', fname
    if fname != '/:::NONEXISTANT:::' and not os.path.exists(fname):
        dbopen()

    if not dbcheckver():
        print 'ERROR: Database version mismatch.'
        return False

    if not trywrite():
        print 'Cannot write to database. Working in :memory:'
        global dbversion
        global conn
        global c
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        dbversion = ':memory:'
        initialize()

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
    fname = fullpath()
    if os.path.exists(fname):
        print 'Removing', fname
        os.remove(fname)

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

CREATE TABLE trywrite (
    tw integer
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

    print 'Stats database initialized'

    if dbversion != ':memory:':
        dbclose()



def fingerprint(name):
    fname = '%s.py' % name
    rdirs = util.get_robot_dirs()
    for d in rdirs:
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
    try:
        c.execute(q, locals())
        conn.commit()
    except sqlite3.OperationalError:
        conn.rollback()



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
    try:
        c.execute(q, locals())
        conn.commit()
    except sqlite3.OperationalError:
        conn.rollback()

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


def top10():
    q = '''
    SELECT
        program_name,
        fingerprint,
        matches,
        wins,
        opponents,
        kills,
        damage_caused

    FROM stats
    ORDER BY
        wins DESC,
        kills DESC

    '''

    c.execute(q, locals())
    results = c.fetchall()

    print 'Top 10 List:'
    if dbversion == ':memory:':
        fname = dbversion
    else:
        fname = fullpath()
    print '(%s)' % fname
    for n, line in enumerate(results[:10]):
        print n+1, '::', line[0], ':', line[3], 'wins', ':', line[5], 'defeated', ':', line[6], 'dmg caused'


if __name__ == '__main__':
    dbopen()
    top10()
