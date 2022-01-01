import random
from flask import Flask, render_template, send_from_directory, request, redirect, url_for, session

from database import *
from manga_service import get_mangadex_covers

app = Flask(__name__, static_url_path='', static_folder='static')
app.secret_key = "lol"
rounds = [2, 4, 8, 16]

@app.route('/demo', methods=['GET', 'POST'])
def demo():
    if request.method == 'GET':
        return render_template('demo.html', **locals())


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        mangas = get_all_mangas()
        return render_template('index.html', **locals())


@app.route('/list', methods=['GET', 'POST'])
def list(manga="Death Note"):
    if request.method == 'POST':
        delete_manga(request.form.get('cover_url'))
    mangas = get_all_mangas()
    return render_template('list.html', **locals())


@app.route('/manga/<mid>/<int:volume>', methods=['GET'])
@app.route('/manga/<mid>', methods=['GET'])
def manga_index(mid=None, volume=1):
    if mid is None:
        return redirect(url_for('index'))
    manga = get_manga(mid)
    cover = get_cover(mid, volume)
    next_volume_number = get_next_volume(volume, len(manga))
    previous_volume_number = get_previous_volume(volume, len(manga))
    return render_template('manga.html', **locals())


@app.route('/tier/manga/<mid>/<int:volume>', methods=['GET', 'POST'])
@app.route('/tier/manga/<mid>', methods=['GET', 'POST'])
def manga_cover_tier(mid=None, volume=1):
    if mid is None:
        return redirect(url_for('index'))
    else:
        manga = get_manga(mid)
        tiers = {
            "S": {
                "label": "Incroyable",
                "volumes": get_tier(mid, "S"),
                "color": "#A23B72"
            },
            "A": {
                "label": "Wow",
                "volumes": get_tier(mid, "A"),
                "color": "#C73E1D"
            },
            "B": {
                "label": "Belle",
                "volumes": get_tier(mid, "B"),
                "color": "#fb6107"
            },
            "C": {
                "label": "Sympa",
                "volumes": get_tier(mid, "C"),
                "color": "#52b69a"
            },
            "D": {
                "label": "Ok",
                "volumes": get_tier(mid, "D"),
                "color": "#0096C7"
            },
            "E": {
                "label": "Bof",
                "volumes": get_tier(mid, "E"),
                "color": "#0077B6"
            },
            "F": {
                "label": "Nulle",
                "volumes": get_tier(mid, "F"),
                "color": "#023E8A"
            }
        }
        empty_tier = get_tier(mid, '')
        cover = get_cover(mid, volume)
        next_volume_number = get_next_volume(volume, len(manga))
        previous_volume_number = get_previous_volume(volume, len(manga))

        if request.method == 'GET':
            t = (mid, volume)
            db = get_db()
            db.row_factory = sqlite3.Row
            c= db.cursor()
            c.execute('SELECT * FROM reviews WHERE uid=? and volume=?', t)
            entry = c.fetchone()
            if entry is not None:
                volume_already_noted = True
            return render_template('tier.html', **locals())
        else:
            note_tier = request.form.get('note_tier')
            volume_number = request.form.get('volume_number')
            update_tier(mid, volume_number, note_tier)
            return redirect(url_for('manga_cover_tier', mid=mid, volume=next_volume_number))


@app.route('/note/manga/<mid>/<int:volume>', methods=['GET', 'POST'])
@app.route('/note/manga/<mid>', methods=['GET', 'POST'])
def manga_cover_review(mid=None, volume=1):

    if mid is None:
        return redirect(url_for('index'))
    else:
        top_3 = get_top(mid)
        manga = get_manga(mid)
        cover = get_cover(mid, volume)
        next_volume_number = get_next_volume(volume, len(manga))
        previous_volume_number = get_previous_volume(volume, len(manga))

        if request.method == 'GET':
            t = (mid, volume)
            db = get_db()
            db.row_factory = sqlite3.Row
            c= db.cursor()
            c.execute('SELECT * FROM reviews WHERE uid=? and volume=?', t)
            entry = c.fetchone()
            if entry is not None:
                volume_already_noted = True
            return render_template('note.html', **locals())
        else:
            note_1 = request.form.get('note_1')
            note_2 = request.form.get('note_2')
            note_3 = request.form.get('note_3')
            volume_number = request.form.get('volume_number')
            update_notes(mid, volume_number, note_1, note_2, note_3)
            return redirect(url_for('manga_cover_review', mid=mid, volume=next_volume_number))


# TODO : Randomize order and check cause points are counted between rounds..
@app.route('/clash/manga/<mid>/<int:stage>/<int:round>', methods=['GET', 'POST'])
@app.route('/clash/manga/<mid>', methods=['GET', 'POST'])
def manga_cover_clash(mid=None,stage=0, round=0):
    round = round
    stage = stage
    manga = mid
    idx = 2 * round
    manga = get_manga(mid)

    if request.method == 'GET':
        stages = 2
        while len(manga) >= 2**stages:
            stages += 1

        if stage == stages:
            return redirect(url_for('manga_cover_clash_results', mid=mid))

        if round == 0:
            if stage == 0: # Qualifications
                bracket = get_top(mid, 1000)
            else:
                bracket = get_top(mid, 2 ** (stages - stage))
            random.shuffle(bracket)
            session['bracket'] = bracket

        bracket = session['bracket']

        if idx > (len(session['bracket']) - 1):
            return redirect(url_for('manga_cover_clash', mid=mid, stage=int(stage)+1, round=0))

        clashCover1 = session['bracket'][idx]
        clashCover2 = session['bracket'][idx + 1] if idx + 1 < len(session['bracket']) else None
        return render_template('clash.html', **locals())
    else:
        v1 = request.form.get('volume1')
        v2 = request.form.get('volume2')
        pts = int(request.form.get('points'))
        v1points = 100 - pts
        v2points = pts
        update_points(mid, v1, v1points)
        if idx + 1 < len(session['bracket']):
            update_points(mid, v2, v2points)
        return redirect(url_for('manga_cover_clash', mid=mid, stage=stage, round=round+1))


@app.route('/results/manga/<mid>')
@app.route('/results/manga/<mid>/<int:volume>')
def manga_cover_clash_results(mid=None, volume=1):
    manga = get_manga(mid)
    top = get_complete_top(mid, 100)
    cover = get_cover(mid, volume)
    return render_template('results.html', **locals())


@app.route('/results')
@app.route('/results/<mid>/<int:volume>')
def manga_cover_clash_overall_results(mid=None, volume=1):
    top = get_overall_top(100)
    cover = None
    if mid is not None:
        cover = get_cover(mid, volume)
    return render_template('results.html', **locals())


@app.route('/load', methods=['GET', 'POST'])
def load_new_manga():
    if request.method == 'GET':
        return render_template('load.html')
    else:
        mangaName = request.form.get('name')
        mangadexId = request.form.get('id')
        title, volumes, covers = get_mangadex_covers(mangaName, mangadexId)
        seed_data(mangadexId, title, covers)
        return redirect(url_for('index'))


def get_next_volume(volume, max):
    return 1 if volume == max else (volume + 1)


def get_previous_volume(volume, max):
    return max if volume == 1 else (volume - 1)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == "__main__":
    pass
