from os import environ

import asyncio
import secrets
from datetime import datetime

import aiosqlite
import fastapi
import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.background import BackgroundTask
from starlette.middleware.cors import CORSMiddleware

# from mounts.discord import app as DiscordApp
from staticfiles import StaticFiles

load_dotenv()
environ.setdefault("ADMIN_USERNAME", "admin")
environ.setdefault("ADMIN_PASSWORD", "0001")
environ.setdefault("BOT_TOKEN", "")


app = FastAPI()
# app.mount("/", DiscordApp)
security = HTTPBasic()


def verify_admin(realm: str = ""):
    def function(c: HTTPBasicCredentials = Depends(security)):
        correct_username = secrets.compare_digest(c.username, environ["ADMIN_USERNAME"])
        correct_password = secrets.compare_digest(c.password, environ["ADMIN_PASSWORD"])
        authed = (correct_username and correct_password)
        if correct_username is False or correct_password is False:
            raise HTTPException(
                401,
                detail="Incorrect username or password",
                headers={
                    "WWW-Authenticate": "Basic, realm=\"{}\"".format(realm.replace("\"", r"\""))
                }
            )
        return authed
    return function


app.state.loop = asyncio.get_event_loop()
app.state.db = app.state.loop.run_until_complete(aiosqlite.connect("./data.base"))
app.state.loop.run_until_complete(
    app.state.db.execute(
        """
        CREATE TABLE IF NOT EXISTS referrers (
            id TEXT PRIMARY KEY NOT NULL UNIQUE,
            referrals INTEGER,
            source TEXT NOT NULL CHECK (source IN (query|header))
        );
        """
    )
)

cached_invite = {"url": None, "created_at": None}


# noinspection PyTypeChecker
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


# async def add_referral(key: str, table_name: str = "referrals"):


@app.get("/favicon.ico")
def get_icon():
    return fastapi.responses.RedirectResponse("/html/assets/avatar.png", 308, {"Cache-Control": "max-age=806400"})


@app.get("/goodbye")
def goodbye():
    return fastapi.responses.RedirectResponse("https://discord.gg/FBygPcymed?event=923623597489156167", 308)


@app.get("/avatar.png", include_in_schema=False)
def get_avatar(_format: str = "webp"):
    if not environ["BOT_TOKEN"]:
        raise HTTPException(503)
    if _format not in ["webp", "png"]:
        raise HTTPException(400)
    try:
        response = requests.get(
            "https://discord.com/api/users/619328560141697036",
            headers={
                "Authorisation": "Bot " + environ["BOT_TOKEN"]
            }
        )
        return "https://cdn.discordapp.com/avatars/619328560141697036/{}.{}".format(
            response.json()["avatar"],
            _format
        )
    except Exception:
        return f"https://cdn.discordapp.com/embed/avatars/{5601%5}.png"

@app.get("/bot-stats")
def stats():
    return requests.get("https://api.yourapps.cyou/meta/stats").json()


@app.get("/commands")
def commands():
    return fastapi.responses.HTMLResponse(
        open("html/commands.html").read(),
        200,
        {"Cache-Control": "public,max-age=806400"},
    )
    # we can cache this for ages since the page itself is dynamic.


@app.get("/stats")
async def statistics(authorized: bool = Depends(verify_admin("Analytics"))):
    if authorized is False:
        # depends should automatically return the forbidden header if auth failed
        raise HTTPException(500, detail={"detail": "Unexpected condition. Failing for security reasons."})

    data = {}

    async with aiosqlite.connect("./data.base") as connection:
        connection.row_factory = aiosqlite.Row
        async for row in await connection.execute("""SELECT id, referrals FROM referrers ORDER BY referrals DESC;"""):
            data[row["id"]] = row["referrals"]

    return fastapi.responses.JSONResponse(
        data
    )


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


# Mount stuff
app.add_middleware(CORSMiddleware, allow_origins=["https://*.dragdev.xyz", "https://yourapps.cyou"],
                   allow_methods=["GET", "POST"])
app.mount("/html", StaticFiles(directory="html", html=True))
app.mount("/", StaticFiles(directory="html", html=True))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", forwarded_allow_ips="*", proxy_headers=True, port=9126)
