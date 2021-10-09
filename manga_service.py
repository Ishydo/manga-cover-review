import requests
from bs4 import BeautifulSoup


def get_mangadex_covers(name="Naruto", id="6b1eb93e-473a-4ab3-9922-1a66d2a29a4a"):
    base_url = "https://uploads.mangadex.org/covers"
    r = requests.get('https://api.mangadex.org/cover?manga[]={0}&limit=100&order[volume]=asc'.format(id))
    
    print(r.json()['data'])

    filtered = list(filter(lambda x: str(x['attributes']['volume']).isnumeric() and x != "0", r.json()['data']))
    nbVolumes = len(filtered)

    covers = []
    for cover in filtered:
        covers.append({
            "title": "{0} #{1}".format(name, cover['attributes']['volume']),
            "volume": cover['attributes']['volume'],
            "url": "{0}/{1}/{2}".format(base_url, id, cover['attributes']['fileName']),
            "notes": {
                "note_1": 0,
                "note_2": 0,
                "note_3": 0
            },
            "points": 0
        })
    print("{0} volumes fetched.".format(nbVolumes))
    return name, nbVolumes, covers
