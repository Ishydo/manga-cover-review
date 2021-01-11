import requests
import sqlite3

from flask import Flask,render_template, send_from_directory, request, g, redirect,url_for
from datetime import datetime
from bs4 import BeautifulSoup

app = Flask(__name__)
conn = sqlite3.connect('mangacoverreview.db')

MANGA_NAME = "Bleach"
COVERS_URL = "https://mangadex.org/title/35/bleach/covers/"
VOLUMES_LIMIT = 74

# 'https://mangadex.org/title/5/naruto/covers/' https://mangadex.org/title/39/one-piece/covers/


DATABASE = 'mangacoverreview.db'


@app.route('/assets/<path:path>')
def send_js(path):
    return send_from_directory('assets', path)


@app.route('/', methods=['GET', 'POST'])
@app.route('/<volume>', methods=['GET', 'POST'])
def manga_cover_review(volume=1):

    manga = MANGA_NAME
    volume_number = volume
    next_volume_number = get_next_volume(volume_number)
    previous_volume_number = get_previous_volume(volume_number)
    cover = get_single_cover(COVERS_URL, volume_number)
    top_3 = get_top()

    if request.method == 'GET':
        t = (MANGA_NAME, volume_number)
        db = get_db()
        db.row_factory = sqlite3.Row
        c= db.cursor()
        c.execute('SELECT * FROM reviews WHERE manga=? and volume=?', t)
        entry = c.fetchone()
        if entry is not None:
            volume_already_noted = True
        return render_template('index.html', **locals())
    else:
        note_1 = request.form.get('note_1')
        note_2 = request.form.get('note_2')
        note_3 = request.form.get('note_3')
        volume_number = request.form.get('volume_number')

        db = get_db()
        c = db.cursor()
        c.execute("INSERT INTO reviews VALUES ('{}','{}',{},'{}',{},{},{})".format(
           datetime.now(),
           MANGA_NAME,
           volume_number,
           cover,
           note_1,
           note_2,
           note_3 
        ))
        db.commit()

        return redirect(url_for('manga_cover_review', volume=next_volume_number))


def get_next_volume(volume):
    return 1 if volume == "{0}".format(VOLUMES_LIMIT) else "{0}".format(int(volume) + 1)


def get_previous_volume(volume):
    return VOLUMES_LIMIT if volume == "1" else "{0}".format(int(volume) - 1)


def get_single_cover(url , volume):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    volume_object = soup.find("div", {"id": "volume_{0}".format(volume)})
    return volume_object.a["href"]


def get_all_covers(url):

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    volumes = soup.find_all("div", id=lambda value: value and value.startswith("volume_"))

    covers = []

    for volume in volumes:
        covers.append({
            "id": "0",
            "url": volume.a["href"].split("?")[0] 
        })

    return covers


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

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
             note_3 float)''')
        db.commit()


def get_top(podium=3):
    t = (MANGA_NAME,)
    db = get_db()
    db.row_factory = sqlite3.Row
    c= db.cursor()
    c.execute('SELECT *, ((note_1 + note_2 + note_3) / 3.0) as avg FROM reviews WHERE manga=? ORDER BY avg DESC LIMIT 3', t)
    entries = c.fetchall()
    return entries


if __name__ == "__main__":
    
    init_db()
    #get_top()