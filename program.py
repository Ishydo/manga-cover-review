
import random
from flask import Flask, render_template, send_from_directory, request, redirect, url_for, session

from crawler import get_manga_news_crawling, get_mangadex_covers
from database import *
from config import MANGA_INFOS_URL

app = Flask(__name__)
app.secret_key = "lol"

@app.route('/config', methods=['GET', 'POST'])
def config_manga():
	if request.method == 'GET':
		return render_template('config.html')
	else:
		url = request.form.get('manga')
		global MANGA_TITLE, MANGA_VOLUMES_NUMBER, MANGA_COVERS_ARRAY, ALL_FIRST_ROUND_COVERS, CLASH_BRACKET
		MANGA_TITLE, MANGA_VOLUMES_NUMBER, MANGA_COVERS_ARRAY = get_manga_news_crawling(url)
		ALL_FIRST_ROUND_COVERS = get_round_covers(MANGA_TITLE, 0)
		CLASH_BRACKET = list(ALL_FIRST_ROUND_COVERS); random.shuffle(CLASH_BRACKET)
		return redirect(url_for('manga_cover_review', volume=1))

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


@app.route('/clash', methods=['GET', 'POST'])
@app.route('/clash/<int:pool>/<int:round>', methods=['GET', 'POST'])
def manga_cover_clash(pool=0, round=0):
	round = round

	if pool == 0:
		ALL_FIRST_ROUND_COVERS = get_round_covers(session['manga'], 0)
		CLASH_BRACKET = list(ALL_FIRST_ROUND_COVERS); random.shuffle(CLASH_BRACKET)
		bracket = CLASH_BRACKET
	else:
		print("NEW ROUND STARTING")
		bracket = get_round_covers(session['manga'], pool)
		print(bracket)
		if not bracket:
			return redirect(url_for('manga_cover_clash_results'))

	idx = 2 * round

	if idx > (len(bracket) - 2):
		return redirect(url_for('manga_cover_clash', pool=int(pool)+1, round=0))

	clashCover1 = bracket[idx]
	clashCover2 = bracket[idx + 1]

	if request.method == 'GET':
		return render_template('clash.html', **locals())
	else:
		winner =  request.form.get('volume')
		update_points(winner)
		return redirect(url_for('manga_cover_clash', pool=pool, round=round+1))

@app.route('/results')
def manga_cover_clash_results():
	manga = session['manga']
	top = get_top(manga, 100)
	return render_template('results.html', **locals())


@app.route('/', methods=['GET', 'POST'])
@app.route('/<int:volume>', methods=['GET', 'POST'])
def manga_cover_review(volume=1):

	if 'manga' not in session:
		return redirect(url_for('choose'))
	else:
		manga = session['manga']
		next_volume_number = get_next_volume(volume)
		previous_volume_number = get_previous_volume(volume)
		top_3 = get_top(manga)
		print(session['manga'])
		cover = get_cover(manga, volume)

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
    #get_mangadex_covers()
