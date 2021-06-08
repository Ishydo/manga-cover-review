import requests
from bs4 import BeautifulSoup

def get_mangadex_covers(name="Naruto", id="6b1eb93e-473a-4ab3-9922-1a66d2a29a4a"):
	base_url = "https://uploads.mangadex.org/covers"
	r = requests.get('https://api.mangadex.org/cover?manga[]={0}&limit=100&order[volume]=asc'.format(id))
	
	filtered = list(filter(lambda x: str(x['data']['attributes']['volume']).isnumeric(), r.json()['results']))
	nbVolumes = len(filtered)

	covers = []
	for cover in filtered:
		covers.append({
			"title": "{0} #{1}".format(name, cover['data']['attributes']['volume']),
			"volume": cover['data']['attributes']['volume'],
			"url": "{0}/{1}/{2}".format(base_url, id, cover['data']['attributes']['fileName']),
			"notes": {
				"note_1": 0,
				"note_2": 0,
				"note_3": 0
			},
			"points": 0
		})
	print("{0} volumes fetched.".format(nbVolumes))
	return name, nbVolumes, covers



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