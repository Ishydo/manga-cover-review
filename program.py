import requests

from flask import Flask,render_template, send_from_directory, request
from bs4 import BeautifulSoup

app = Flask(__name__)

MANGA_NAME = "Bleach"
COVERS_URL = "https://mangadex.org/title/35/bleach/covers/"
# 'https://mangadex.org/title/5/naruto/covers/' https://mangadex.org/title/39/one-piece/covers/


@app.route('/assets/<path:path>')
def send_js(path):
    return send_from_directory('assets', path)


@app.route('/')
@app.route('/<volume>', methods=['GET', 'POST'])
def hello_world(volume=1):

    if request.method == 'GET':
        manga = MANGA_NAME
        volume_number = volume
        next_volume_number = "{0}".format(int(volume) + 1)
        cover = get_single_cover(COVERS_URL, volume_number)

        return render_template('index.html', **locals())
    else:
        pass



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

if __name__ == "__main__":
    
    page = requests.get(COVERS_URL)
    soup = BeautifulSoup(page.content, 'html.parser')

    covers = soup.find_all("div", id=lambda value: value and value.startswith("volume_"))

    for cover in covers:
        cover_id = cover.a.img["alt"].split(" ")[1] 
        cover_url = cover.a["href"].split("?")[0]

        print("{0} #{1}".format(MANGA_NAME, cover_id))
        print(cover_url)