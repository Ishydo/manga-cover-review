import sqlite3
from flask import Flask, g

app = Flask(__name__)
DATABASE = 'mangacoverreview.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with app.app_context():
        db = get_db()
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

def seed_data():
    with app.app_context(manga_title, mangas):
        db = get_db()
        c = db.cursor()
        for manga_volume in mangas:
            c.execute("INSERT INTO reviews VALUES ('{}','{}',{},'{}',{},{},{},{})".format(datetime.now(), manga_title, manga_volume['volume'], manga_volume['url'], 0, 0, 0, 0))
            db.commit()

def update_notes(volume, note_1, note_2, note_3):
    with app.app_context():
        db = get_db()
        c = db.cursor()
        c.execute("UPDATE reviews SET `note_1` = {}, `note_2` = {}, `note_3` = {} WHERE `volume` = {}".format(note_1, note_2, note_3, volume))
        db.commit()

def update_points(volume):
    with app.app_context():
        db = get_db()
        c = db.cursor()
        c.execute("UPDATE reviews SET `points` = `points` + 1 WHERE `volume` = {}".format(volume))
        db.commit()

def get_top(manga_title, podium=3):
    t = (manga_title,)
    db = get_db()
    db.row_factory = sqlite3.Row
    c= db.cursor()
    c.execute('SELECT *, ((note_1 + note_2 + note_3) / 3.0) as avg FROM reviews WHERE manga=? ORDER BY avg DESC LIMIT 3', t)
    entries = c.fetchall()
    return entries

def get_round_covers(manga_title, round):
    t = (manga_title, round)
    db = get_db()
    db.row_factory = sqlite3.Row
    c= db.cursor()
    c.execute('SELECT * FROM reviews WHERE `manga`=? AND `points`=?', t)
    entries = c.fetchall()
    return entries