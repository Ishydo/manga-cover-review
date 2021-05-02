import requests
from bs4 import BeautifulSoup

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