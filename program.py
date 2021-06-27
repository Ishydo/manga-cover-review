import random
from flask import Flask, render_template, send_from_directory, request, redirect, url_for, session

from database import *
from manga_service import get_mangadex_covers

app = Flask(__name__, static_url_path='', static_folder='static')
app.secret_key = "lol"
rounds = [2, 4, 8, 16]


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
        return redirect(url_for('choose'))
    manga = get_manga(mid)
    tiers = {
        "S": get_tier(mid, "S"),
        "A": get_tier(mid, "A"),
        "B": get_tier(mid, "B"),
        "C": get_tier(mid, "C"),
        "D": get_tier(mid, "D"),
        "E": get_tier(mid, "E"),
        "F": get_tier(mid, "F"),
    }
    cover = get_cover(mid, volume)
    next_volume_number = get_next_volume(volume, len(manga))
    previous_volume_number = get_previous_volume(volume, len(manga))
    return render_template('manga.html', **locals())


@app.route('/tier/manga/<mid>/<int:volume>', methods=['GET', 'POST'])
@app.route('/tier/manga/<mid>', methods=['GET', 'POST'])
def manga_cover_tier(mid=None, volume=1):
    if mid is None:
        return redirect(url_for('choose'))
    else:
        manga = get_manga(mid)
        tiers = {
            "S": get_tier(mid, "S"),
            "A": get_tier(mid, "A"),
            "B": get_tier(mid, "B"),
            "C": get_tier(mid, "C"),
            "D": get_tier(mid, "D"),
            "E": get_tier(mid, "E"),
            "F": get_tier(mid, "F"),
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
        return redirect(url_for('choose'))
    else:
        top_3 = get_top(mid)
        cover = get_cover(mid, volume)
        next_volume_number = get_next_volume(volume)
        previous_volume_number = get_previous_volume(volume)

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
            update_notes(volume_number, note_1, note_2, note_3)
            return redirect(url_for('manga_cover_review', volume=next_volume_number))


# TODO : Randomize order and check cause points are counted between rounds..
@app.route('/clash/manga/<mid>/<int:stage>/<int:round>', methods=['GET', 'POST'])
def manga_cover_clash(mid=None,stage=0, round=0):
    round = round
    stage = stage
    manga = mid
    idx = 2 * round

    if request.method == 'GET':
        stages = 2
        while int(session['volumes']) >= 2**stages:
            stages += 1

        if stage == stages:
            return redirect(url_for('manga_cover_clash_results'))

        if round == 0:
            print("round0")
            if stage == 0: # Qualifications
                print("stage0")
                bracket = get_top(session['manga'], 1000)
            else:
                bracket = get_top(session['manga'], 2 ** (stages - stage))
            random.shuffle(bracket)
            session['bracket'] = bracket

        bracket = session['bracket']

        if idx > (len(session['bracket']) - 1):
            return redirect(url_for('manga_cover_clash', stage=int(stage)+1, round=0))

        clashCover1 = session['bracket'][idx]
        clashCover2 = session['bracket'][idx + 1] if idx + 1 < len(session['bracket']) else None
        return render_template('clash.html', **locals())
    else:
        v1 = request.form.get('volume1')
        v2 = request.form.get('volume2')
        pts = int(request.form.get('points'))
        v1points = 100 - pts
        v2points = pts
        update_points(session['manga'], v1, v1points)
        if idx + 1 < len(session['bracket']):
            update_points(session['manga'], v2, v2points)
        return redirect(url_for('manga_cover_clash', stage=stage, round=round+1))


@app.route('/results')
def manga_cover_clash_results():
    manga = session['manga']
    top = get_top(manga, 100)
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
        return render_template('load.html')


@app.route('/choose', methods=['GET', 'POST'])
def choose():
    if request.method == 'GET':
        mangas = get_all_mangas()
        return render_template('choose.html', **locals())


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
