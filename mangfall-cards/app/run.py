"""Install the MANGFALL cards into Home Assistant and exit.

Runs once at every Home Assistant start (startup: once, boot: auto):
1. copies mangfall-cards.js to /config/www/mangfall/,
2. registers it as a dashboard resource (module) with a version query so browsers reload it,
3. leaves the system alone if the cards already come from somewhere else (HACS or a custom file).

A copy installed by Haglo Assist (/local/haglo/mangfall-cards.js) is taken over, so only one copy is loaded.
Nothing is sent anywhere except to the local Home Assistant.
"""

import asyncio
import os
import re
import sys
from pathlib import Path

import aiohttp

SRC = Path(__file__).parent / "mangfall-cards.js"
CONFIG = Path("/homeassistant")
DST = CONFIG / "www" / "mangfall" / "mangfall-cards.js"
URL = "/local/mangfall/mangfall-cards.js"
LIB = "mangfall-cards"
TAKE_OVER = ("/local/haglo/mangfall-cards.js",)  # older copies from Haglo Assist
WS_URL = "ws://supervisor/core/websocket"
TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")
AUTO_UPDATE_MARK = Path("/data/auto_update_on")


def log(msg: str) -> None:
    print(f"[MANGFALL] {msg}", flush=True)


def version() -> str:
    m = re.search(r'MC_VERSION\s*=\s*"([^"]+)"', SRC.read_text(encoding="utf-8"))
    return m.group(1) if m else "1"


def stem(url: str) -> str:
    """/hacsfiles/mangfall-cards/mangfall-cards.js?hacstag=1 -> mangfall-cards"""
    s = url.split("?", 1)[0].split("#", 1)[0].rstrip("/").rsplit("/", 1)[-1].lower()
    s = re.sub(r"\.(js|mjs)$", "", s)
    return re.sub(r"([.-](min|bundle|umd|es|module))+$", "", s)


def plan(resources: list, url: str) -> dict:
    """Decide what to do with the existing dashboard resources (pure function, tested)."""
    path = lambda r: str(r.get("url") or "").split("?", 1)[0]
    mine = [r for r in resources if path(r) == URL]
    old = [r for r in resources if path(r) in TAKE_OVER]
    foreign = [
        r
        for r in resources
        if stem(str(r.get("url") or "")) == LIB and r not in mine and r not in old
    ]
    if foreign:
        return {
            "action": "skip",
            "reason": f"already installed from {path(foreign[0])}",
        }
    keep = (mine or old)[:1]
    drop = [r for r in mine + old if r not in keep]
    if not keep:
        return {"action": "create", "url": url, "drop": drop}
    r = keep[0]
    if r.get("url") != url or r.get("type") != "module":
        return {"action": "update", "id": r["id"], "url": url, "drop": drop}
    return {"action": "none", "drop": drop}


class HA:
    def __init__(self, session):
        self.session, self.ws, self.n = session, None, 0

    async def __aenter__(self):
        self.ws = await self.session.ws_connect(WS_URL, heartbeat=30)
        await self.ws.receive_json()  # auth_required
        await self.ws.send_json({"type": "auth", "access_token": TOKEN})
        if (await self.ws.receive_json()).get("type") != "auth_ok":
            raise RuntimeError("Anmeldung bei Home Assistant abgelehnt")
        return self

    async def __aexit__(self, *exc):
        await self.ws.close()

    async def call(self, msg_type: str, **payload):
        self.n += 1
        await self.ws.send_json({"id": self.n, "type": msg_type, **payload})
        while True:
            msg = await self.ws.receive_json()
            if msg.get("id") == self.n and msg.get("type") == "result":
                if not msg.get("success"):
                    err = msg.get("error") or {}
                    raise RuntimeError(
                        f"{err.get('code', 'error')}: {err.get('message', '')}"
                    )
                return msg.get("result")


async def served(session, url: str) -> bool | None:
    for base in ("http://homeassistant:8123", "https://homeassistant:8123"):
        try:
            async with session.get(
                base + url, ssl=False, timeout=aiohttp.ClientTimeout(total=8)
            ) as r:
                return r.status == 200
        except (TimeoutError, aiohttp.ClientError, OSError):
            continue  # try the other scheme; None means "cannot check"
    return None


async def install(session) -> int:
    url = f"{URL}?v={version()}"
    async with HA(session) as ha:
        try:
            resources = await ha.call("lovelace/resources")
        except RuntimeError as e:
            log(
                f"Dashboards im YAML-Modus – bitte die Ressource selbst eintragen: {URL} (Typ: module) – {e}"
            )
            return 0
        p = plan(resources or [], url)
        if p["action"] == "skip":
            log(f"Karten sind schon installiert ({p['reason']}) – nichts zu tun.")
            return 0
        had_www = DST.parent.parent.is_dir()
        data = SRC.read_bytes()
        DST.parent.mkdir(parents=True, exist_ok=True)
        if not DST.exists() or DST.read_bytes() != data:
            DST.write_bytes(data)
        if p["action"] == "create":
            await ha.call("lovelace/resources/create", res_type="module", url=url)
        elif p["action"] == "update":
            await ha.call(
                "lovelace/resources/update",
                resource_id=p["id"],
                res_type="module",
                url=url,
            )
        for r in p["drop"]:
            await ha.call("lovelace/resources/delete", resource_id=r["id"])
    ok = await served(session, url)
    if ok is False or (ok is None and not had_www):
        log("Karten abgelegt – sichtbar nach einem Neustart von Home Assistant.")
    else:
        log(f"Karten bereit ({url}). Im Dashboard: Karte hinzufügen → „MANGFALL“.")
    return 0


async def auto_update(session) -> None:
    """Turn on automatic updates once. If the user switches them off later, that choice stays."""
    if AUTO_UPDATE_MARK.exists():
        return
    try:
        async with session.post(
            "http://supervisor/addons/self/options",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"auto_update": True},
            timeout=aiohttp.ClientTimeout(total=20),
        ) as r:
            if r.status == 200:
                AUTO_UPDATE_MARK.write_text("1")
                log("Automatische Updates eingeschaltet.")
    except (aiohttp.ClientError, OSError, asyncio.TimeoutError):
        pass  # next start tries again


async def main() -> int:
    if not CONFIG.is_dir() or not SRC.is_file() or not TOKEN:
        log("Kein Zugriff auf die Home-Assistant-Konfiguration – Add-on-Rechte prüfen.")
        return 1
    async with aiohttp.ClientSession() as session:
        await auto_update(session)
        for attempt in range(30):  # Home Assistant may still be starting
            try:
                return await install(session)
            except (
                aiohttp.ClientError,
                RuntimeError,
                OSError,
                ValueError,
                TypeError,
            ) as e:
                if attempt == 29:
                    log(f"Einrichtung fehlgeschlagen: {e}")
                    return 1
                await asyncio.sleep(10)
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
