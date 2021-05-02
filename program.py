import requests
import random

from flask import Flask, render_template, send_from_directory, request, redirect,url_for
from datetime import datetime
from bs4 import BeautifulSoup

from crawler import get_manga_news_crawling
from database import *
from config import MANGA_INFOS_URL

app = Flask(__name__)

def get_manga_news_crawling(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    title = soup.find("div", { "id": "breadcrumb" }).find_all('span', recursive=False)[3].find("span").text
    searchImageString = "{0} Vol.".format(title)
    imagesBlocks = soup.find_all("img", alt=lambda alt: alt and alt.startswith(searchImageString))
    nbVolumes = len(imagesBlocks)

    covers = []

    for image in imagesBlocks:
        srcArr = image["src"].split("_m")
        cleanSrc = "{0}{1}".format(srcArr[0].replace("/.", "/"), srcArr[1])
        covers.append({
            "title": image["alt"],
            "volume": int(image["alt"].split(".")[1]),
            "url": cleanSrc,
            "notes": {
                "note_1": 0,
                "note_2": 0,
                "note_3": 0
            },
            "points": 0
    })

    return title, nbVolumes, covers

MANGA_TITLE, MANGA_VOLUMES_NUMBER, MANGA_COVERS_ARRAY = get_manga_news_crawling(MANGA_INFOS_URL)
CLASH_BRACKET = list(MANGA_COVERS_ARRAY); random.shuffle(CLASH_BRACKET)

@app.route('/assets/<path:path>')
def send_js(path):
    return send_from_directory('assets', path)


@app.route('/clash', methods=['GET', 'POST'])
@app.route('/clash/<int:round>', methods=['GET', 'POST'])
def manga_cover_clash(round=0):
    round = round
    manga = MANGA_TITLE
    bracket = CLASH_BRACKET
    idx = 2 * round
    
    if idx > (len(bracket) - 1):
        print("round 1 is over")
        round = 0
        bracket = get_round_covers(MANGA_TITLE, 1)
        print(bracket)
    
    clashCover1 = bracket[idx]
    clashCover2 = bracket[idx + 1]

    if request.method == 'GET':
        return render_template('clash.html', **locals())
    else:
        winner =  request.form.get('volume')
        update_points(winner)
        return redirect(url_for('manga_cover_clash', round=round+1))



@app.route('/', methods=['GET', 'POST'])
@app.route('/<int:volume>', methods=['GET', 'POST'])
def manga_cover_review(volume=1):

    manga = MANGA_TITLE
    volume_number = volume
    next_volume_number = get_next_volume(volume)
    previous_volume_number = get_previous_volume(volume)
    
    #cover = get_single_cover(COVERS_URL, volume_number)
    cover = MANGA_COVERS_ARRAY[volume - 1]["url"] # Offset from url arg and array
    top_3 = get_top(MANGA_TITLE)

    if request.method == 'GET':
        t = (MANGA_TITLE, volume)
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
        update_notes(volume_number, note_1, note_2, note_3)
        return redirect(url_for('manga_cover_review', volume=next_volume_number))


def get_next_volume(volume):
    return 1 if volume == MANGA_VOLUMES_NUMBER else (volume + 1)


def get_previous_volume(volume):
    return MANGA_VOLUMES_NUMBER if volume == 1 else (volume - 1)


def get_single_cover(url , volume):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    volume_object = soup.find("div", {"id": "volume_{0}".format(volume)})
    return volume_object.a["href"]

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == "__main__":
    
    init_db()
    seed_data(MANGA_TITLE, MANGA_COVERS_ARRAY)
