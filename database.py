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
            manga varchar(255),
            volume int,
            cover_url text,
            note_1 float,
            note_2 float,
            note_3 float,
            points int)''')
    db.commit()


def seed_data(manga_title, mangas):
    db = get_db()
    c = db.cursor()
    for manga_volume in mangas:
        c.execute("INSERT INTO reviews VALUES ('{}','{}',{},'{}',{},{},{},{})".format(datetime.now(), manga_title, manga_volume['volume'], manga_volume['url'], 0, 0, 0, 0))
        db.commit()


def update_notes(volume, note_1, note_2, note_3):
    db = get_db()
    c = db.cursor()
    c.execute("UPDATE reviews SET `note_1` = {}, `note_2` = {}, `note_3` = {} WHERE `volume` = {}".format(note_1, note_2, note_3, volume))
    db.commit()


def update_points(volume):
    db = get_db()
    c = db.cursor()
    c.execute("UPDATE reviews SET `points` = `points` + 1 WHERE `volume` = {}".format(volume))
    db.commit()


def get_all_mangas():
    db = get_db()
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute('SELECT * FROM reviews ORDER BY manga ASC')
    entries = c.fetchall()
    return entries

def get_manga(manga_title):
    t = (manga_title,)
    db = get_db()
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute('SELECT * FROM reviews WHERE manga=? ORDER BY volume ASC', t)
    entries = c.fetchall()
    return entries

def delete_manga(cover_url):
    db = get_db()
    c = db.cursor()
    c.execute("DELETE from reviews WHERE `cover_url` = '{0}'".format(cover_url))
    db.commit()

def get_cover(manga_title, volume):
    t = (manga_title, volume)
    db = get_db()
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute('SELECT cover_url FROM reviews WHERE manga=? AND volume=?', t)
    entries = c.fetchone()
    return entries


def get_manga_names():
    db = get_db()
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute('SELECT manga, count(manga) as volumes FROM reviews GROUP BY manga ORDER BY manga ASC')
    entries = c.fetchall()
    return entries


def get_top(manga_title, podium=3):
    t = (manga_title, podium)
    db = get_db()
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute('SELECT *, ((note_1 + note_2 + note_3) / 3.0) as avg FROM reviews WHERE manga=? ORDER BY points DESC, avg DESC LIMIT ?', t)
    entries = c.fetchall()
    return entries


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
