import sqlite3
import os.path
from datetime import datetime
from flask import Flask, g

app = Flask(__name__)
DATABASE = 'mangacoverreview.db'


def get_db():
    if not os.path.isfile(DATABASE):
        init_db()
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def init_db():
    db = g._database = sqlite3.connect(DATABASE)
    c = db.cursor()
    c.execute('''CREATE TABLE reviews
            (date datetime,
			uid varchar(255),
            manga varchar(255),
            volume int,
            cover_url text,
            note_1 float,
            note_2 float,
            note_3 float,
            note_tier varchar(255),
            points int)''')
    db.commit()


def seed_data(id, manga_title, mangas):
    db = get_db()
    c = db.cursor()
    for manga_volume in mangas:
        c.execute("INSERT INTO reviews VALUES ('{}','{}','{}',{},'{}',{},{},{},'{}',{})".format(datetime.now(), id, manga_title, manga_volume['volume'], manga_volume['url'], 0, 0, 0, '', 0))
        db.commit()


def update_notes(volume, note_1, note_2, note_3):
    db = get_db()
    c = db.cursor()
    c.execute("UPDATE reviews SET `note_1` = {}, `note_2` = {}, `note_3` = {} WHERE `volume` = {}".format(note_1, note_2, note_3, volume))
    db.commit()


def update_tier(mid, volume, tier):
    db = get_db()
    c = db.cursor()
    c.execute("UPDATE reviews SET `note_tier` = '{}' WHERE `uid` = '{}' AND `volume` = {}".format(tier, mid, volume))
    db.commit()


def update_points(manga, volume, points):
    db = get_db()
    c = db.cursor()
    c.execute("UPDATE reviews SET `points` = `points` + {0} WHERE `manga` = '{1}' AND `volume` = '{2}'".format(int(points), manga, volume))
    db.commit()


def get_all_mangas():
    db = get_db()
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute('SELECT * FROM reviews GROUP BY uid ORDER BY manga ASC')
    entries = c.fetchall()
    return entries


def get_manga(mid):
    t = (mid,)
    db = get_db()
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute('SELECT * FROM reviews WHERE uid=? ORDER BY volume ASC', t)
    entries = c.fetchall()
    return entries


def delete_manga(cover_url):
    db = get_db()
    c = db.cursor()
    c.execute("DELETE from reviews WHERE `cover_url` = '{0}'".format(cover_url))
    db.commit()


def get_cover(uid, volume):
    t = (uid, volume)
    db = get_db()
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute('SELECT cover_url FROM reviews WHERE uid=? AND volume=?', t)
    entries = c.fetchone()
    return entries


def get_manga_names():
    db = get_db()
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute('SELECT manga, count(manga) as volumes FROM reviews GROUP BY manga ORDER BY manga ASC')
    entries = c.fetchall()
    return entries


def get_top(uid, podium=3):
    t = (uid, podium)
    db = get_db()
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute('SELECT *, ((note_1 + note_2 + note_3) / 3.0) as avg FROM reviews WHERE uid=? ORDER BY points DESC, avg DESC LIMIT ?', t)

    columns = [column[0] for column in c.description]
    results = []
    for row in c.fetchall():
        results.append(dict(zip(columns, row)))
    return results


def get_tier(mid, tier):
    t = (mid, tier)
    db = get_db()
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute('SELECT * FROM reviews WHERE uid=? AND note_tier=? ORDER BY points DESC', t)

    columns = [column[0] for column in c.description]
    results = []
    for row in c.fetchall():
        results.append(dict(zip(columns, row)))
    return results


def get_round_covers(manga_title, round):
    t = (manga_title, round)
    db = get_db()
    db.row_factory = dict_factory
    c = db.cursor()
    c.execute('SELECT * FROM reviews WHERE `manga`=? AND `points`=?', t)
    entries = c.fetchall()
    return entries


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
