from fastapi import FastAPI
import fastapi
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
import requests
from datetime import datetime
import re

# from dash import app as dash
from staticfiles import StaticFiles
from reviews import find_reviews_section, soupify, scrape
import reviews
import aiosqlite
from starlette.background import BackgroundTask
import traceback
from hmac import HMAC, compare_digest
from hashlib import sha1

app = FastAPI()
app.mount("/html", StaticFiles(directory="html", html=True), name="static")
# app.include_router(dash, prefix="/dash")
cached_invite = {"url": None, "created_at": None}
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"])


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


@app.get("/")
def root():
    # data =
    with open("html/index.html") as rfile:
        return fastapi.responses.HTMLResponse(rfile.read(), 200, {"Cache-Control": "max-age=806400"})


@app.head("/")
def up():
    return fastapi.responses.Response(None, 200,)


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
    u = (
        f"https://discord.com/oauth2/authorize?client_id=619328560141697036"
        f"&scope=bot%20guilds.join%20identify&permissions={perms}&response_type=code&redirect_uri=https%3A%2F%2Fya.clicksminuteper.net%2Fcallbacks%2Fauthorized"
    )
    if not dnt:
        # we only query the database if they're allowing tracking. It's not really tracking but whatever, we'll be nice.
        async def bg():
            async with aiosqlite.connect("./data.base") as conn:
                try:
                    cursor = await conn.execute("SELECT (id, referrals) FROM referrers WHERE id=?", ref.lower())
                    referrer, referrals = await cursor.fetchone()
                    referrals = int(referrals)
                    if not referrer:
                        await conn.execute("INSERT INTO referrers (id, referrals) VALUES (?, 1);", ref)
                    else:
                        await conn.execute("UPDATE referrers SET referrals=?", referrals + 1)
                    await conn.commit()
                except Exception as e:
                    print("Error while editing SQL", e, e.__class__.__name__)
                    traceback.print_exc()

    return fastapi.responses.RedirectResponse(u, 308, {"Cache-Control": "max-age=806400"}, BackgroundTask(bg))


@app.get("/support")
def support():
    return fastapi.responses.RedirectResponse(get_invite(), 308, {"Cache-Control": "max-age=86400"})


@app.get("/admin/stats")
def stats():
    with open("html/stats.html") as file:
        text = file.read()
        return fastapi.responses.HTMLResponse(text)



@app.get("/robots.txt")
def robots():
    return fastapi.responses.RedirectResponse("/html/robots.txt", 308)


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
@app.get("/ratings")
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
@app.get("/ratings/pairs")
def get_reviews_pairs(request: fastapi.Request, bot: int = 619328560141697036, limit: int = 50):
    if limit == -1:
        limit = 999_999_999_999
    soup = _get_reviews(request, bot, return_soup=True)
    pairs = reviews.pair_reviews(soup, limit)
    return fastapi.responses.JSONResponse(
        pairs
    )

@app.post("/push", include_in_schema=False)
async def update_time(req: fastapi.Request):
    # Thank god for https://stackoverflow.com/q/59580376/13202421
    def verify_signature(body):
        received_sign = req.headers.get('X-Hub-Signature').split('sha1=')[-1].strip()
        with open("./config.json") as file:  # this is actually just plain-text
            secret = file.read().strip('"').encode()
        expected_sign = HMAC(key=secret, msg=body, digestmod=sha1).hexdigest()
        return compare_digest(received_sign, expected_sign)
    if not verify_signature(await req.body()):
        return fastapi.responses.Response(None, 403)
    return fastapi.responses.Response()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", forwarded_allow_ips="*", proxy_headers=True, port=9126)
