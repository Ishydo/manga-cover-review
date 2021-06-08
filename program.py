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


@app.route('/', methods=['GET', 'POST'])
@app.route('/<int:volume>', methods=['GET', 'POST'])
def manga_cover_review(volume=1):

    if 'manga' not in session:
        return redirect(url_for('choose'))
    else:
        manga = session['manga']
        top_3 = get_top(manga)
        cover = get_cover(manga, volume)
        next_volume_number = get_next_volume(volume)
        previous_volume_number = get_previous_volume(volume)

        if request.method == 'GET':
            t = (manga, volume)
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

# TODO : Randomize order and check cause points are counted between rounds..
@app.route('/clash', methods=['GET', 'POST'])
@app.route('/clash/<int:stage>/<int:round>', methods=['GET', 'POST'])
def manga_cover_clash(stage=0, round=0):
    round = round
    stage = stage
    manga = session['manga']

    stages = 2
    while int(session['volumes']) >= 2**stages:
        stages += 1

    if stage == 0: # Qualifications
        bracket = get_top(session['manga'], 1000)
    else:
        if stage == stages:
            return redirect(url_for('manga_cover_clash_results'))
        
        toget = 2 ** stage
        bracket = get_top(session['manga'], toget)

    idx = 2 * round

    if idx > (len(bracket) - 2):
        return redirect(url_for('manga_cover_clash', stage=int(stage)+1, round=0))

    clashCover1 = bracket[idx]
    clashCover2 = bracket[idx + 1]

    if request.method == 'GET':
        return render_template('clash.html', **locals())
    else:
        v1 = request.form.get('volume1')
        v2 = request.form.get('volume2')
        pts = int(request.form.get('points'))
        v1points = 100 - pts
        v2points = pts
        update_points(session['manga'], v1, v1points)
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
        seed_data(title, covers)
        return render_template('load.html')


@app.route('/choose', methods=['GET', 'POST'])
def choose():
    if request.method == 'GET':
        mangas = get_manga_names()
        return render_template('choose.html', **locals())
    else:
        session['manga'] = request.form.get('manga')
        session['volumes'] = request.form.get('volumes')
        return redirect(url_for('manga_cover_review'))


def get_next_volume(volume):
    return 1 if volume == int(session['volumes']) else (volume + 1)


def get_previous_volume(volume):
    return int(session['volumes']) if volume == 1 else (volume - 1)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == "__main__":
    pass
