import re
import traceback
import asyncio
from datetime import datetime

import aiosqlite
import fastapi
import requests
import uvicorn
from fastapi import FastAPI
from starlette.background import BackgroundTask
from starlette.middleware.cors import CORSMiddleware

import reviews
from reviews import find_reviews_section, scrape, soupify
from staticfiles import StaticFiles

app = FastAPI()

# Database setup
app.state.loop = asyncio.get_event_loop()
app.state.db = app.state.loop.run_until_complete(aiosqlite.connect("./data.base"))
app.state.loop.run_until_complete(
    app.state.db.execute(
        """
        CREATE TABLE IF NOT EXISTS referrers (
            id TEXT PRIMARY KEY NOT NULL UNIQUE,
            referrals INTEGER
        );
        """
    )
)
app.state.loop.run_until_complete(app.state.db.commit())

cached_invite = {"url": None, "created_at": None}


def get_invite():
    if cached_invite["url"]:
        if (datetime.utcnow() - cached_invite["created_at"]).total_seconds() <= 43200:
            return cached_invite["url"]
    try:
        widget = requests.get("https://discord.com/api/guilds/706271127542038608/widget.json")
        if widget.status_code != 200:
            raise RuntimeError("Widget is disabled.")
        invite = widget.json()["invite"]
        cached_invite["url"] = invite
        cached_invite["created_at"] = datetime.utcnow()
        return invite
    except (KeyError, RuntimeError):
        return "https://discord.gg/T9u3Qcm"


@app.get("/favicon.ico")
def get_icon():
    return fastapi.responses.RedirectResponse("/html/assets/avatar.png", 308, {"Cache-Control": "max-age=806400"})


@app.get("/commands")
def commands():
    return fastapi.responses.HTMLResponse(
        open("html/commands.html").read(),
        200,
        {"Cache-Control": "public,max-age=806400"},
    )
    # we can cache this for ages since the page itself is dynamic.


@app.get("/stats")
def pstats():
    return fastapi.responses.HTMLResponse(
        open("html/pstats.html").read(), 200, {"Cache-Control": "public,max-age=806400"}
    )
    # also dynamic


@app.get("/vote")
def vote_uri():
    return fastapi.responses.HTMLResponse("https://top.gg/bot/619328560141697036/vote", 308)



@app.get("/invite")
def invitebot(ref: str = "No Referrer", dnt: int = fastapi.Header(0), perms: int = 0):
    from urllib.parse import quote
    url = "https://discord.com/oauth2/authorize?client_id={}&permissions={}&scope=bot".format(
        619328560141697036,
        perms
    )
    url += "&response_type=code&redirect_url="+quote("https://api.yourapps.cyou/callbacks/authorized")
    async def bg():
        pass  # prevent nameerror

    if dnt == 0:
        async def bg():
            cursor = await app.state.db.execute("SELECT referrals FROM referrers WHERE id=?;", (ref,))
            count = await cursor.fetchone()
            if not count:
                # This is the first time this source has referred.
                # We need to create a row.
                await app.state.db.execute(
                    """
                    INSERT INTO referrers (id, referrals)
                    VALUES (?, 1);
                    """,
                    (ref,)
                )
            else:
                # Just need to increment
                await app.state.db.execute(
                    """
                    UPDATE referrers
                    SET referrals=`referrals`+1
                    WHERE id=?;
                    """,
                    (ref,)
                )
            await app.state.db.commit()
    return fastapi.responses.RedirectResponse(url, 308, {"Cache-Control": "max-age=806400"}, BackgroundTask(bg))


@app.get("/support")
def support():
    return fastapi.responses.RedirectResponse(get_invite(), 308, {"Cache-Control": "max-age=86400"})


@app.get("/robots.txt")
def robots():
    return fastapi.responses.RedirectResponse("/html/robots.txt", 308)


# Get reviews from top.gg
# NOTE: This is deprecated due to unreliability.
def _get_reviews(request, bot, **kwargs):
    headers = dict(request.headers)
    headers.pop("accept-encoding", None)
    headers.pop("host", None)
    headers["accept"] = "text/html;q=0.9,text/plain;q=0.8"
    
    soup = soupify(scrape("/bot/"+str(bot), headers=headers))
    if kwargs.pop("return_soup", False):
        return soup

    reviews = find_reviews_section(soup, string=kwargs.pop("string", True))
    return reviews


@app.get("/reviews", include_in_schema=False)
@app.get("/ratings", deprecated=True)
def get_reviews(request: fastapi.Request, bot: int = 619328560141697036, partial: bool = False):
    reviews = _get_reviews(request, bot)
    if partial:
        return fastapi.responses.HTMLResponse(reviews, 200, {"Cache-Control": "max-age=3600"})
    with open("./template.html") as rfile:
        doc = rfile.read()
    doc = doc.format(reviews)
    doc = re.sub(r"opacity:[\s]?0[;]?", "", doc)
    return fastapi.responses.HTMLResponse(doc, 200)

@app.get("/reviews/pairs", include_in_schema=False)
@app.get("/ratings/pairs", deprecated=True)
def get_reviews_pairs(request: fastapi.Request, bot: int = 619328560141697036, limit: int = 50):
    if limit == -1:
        limit = 999_999_999_999
    soup = _get_reviews(request, bot, return_soup=True)
    pairs = reviews.pair_reviews(soup, limit)
    return fastapi.responses.JSONResponse(
        pairs
    )

# Mount stuff
app.add_middleware(CORSMiddleware, allow_origins=["https://*.dragdev.xyz", "https://yourapps.cyou"], allow_methods=["GET", "POST"])
app.mount("/html", StaticFiles(directory="html", html=True))
app.mount("/", StaticFiles(directory="html", html=True))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", forwarded_allow_ips="*", proxy_headers=True, port=9126)
