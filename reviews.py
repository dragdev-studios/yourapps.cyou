from bs4 import BeautifulSoup
from requests import get  # this can be sync
from datetime import datetime, timedelta

cached = {}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.5",
    "Cache-Control": "no-cache",
    "Host": "top.gg",
    "DNT": "1",
}


def scrape(uri: str = "/bot/619328560141697036", headers=None):
    # with open("export.html", encoding="utf-8", errors="replace") as rfile:
    #     return rfile.read()
    if headers is None:
        headers = DEFAULT_HEADERS
    if uri in cached.keys():
        if cached[uri]["expires"] >= datetime.utcnow():
            return cached[uri]["content"]
        del cached[uri]
    html = get("https://top.gg" + uri, headers=headers).text
    cached[uri] = {
        "content": html,
        "expires": datetime.utcnow()+timedelta(hours=3)
    }
    return html


def soupify(html: str):
    return BeautifulSoup(html, "html.parser")


def find_reviews_section(soup, string: bool = True, clean_hidden: bool = True):
    results = soup.find_all("div", "reviews__wrapper")
    if not results:
        return soup.prettify()
    if not string:
        return results[0]
    found = str(results[0])
    if clean_hidden:
        found = found.replace("opacity:0;", "")
    return found


def find_review_contents(soup, limit: int = 1):
    section = find_reviews_section(soup, string=False)
    return section.find_all("p", "comment-content", limit=limit)

def find_review_authors(soup, limit: int = 1):
    section = find_reviews_section(soup, string=False)
    return section.find_all("p", "review__username", limit=limit)

def pair_reviews(soup, limit: int = 1):
    n = []
    usernames = find_review_authors(soup, limit)
    contents = find_review_contents(soup, limit)
    for index, username in enumerate(usernames):
        n[index] = (username, contents[index])
    return n


if __name__ == "__main__":
    find_reviews_section(soupify(scrape()))
