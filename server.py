import asyncio
import sqlite3
import aiosqlite
from aiohttp import web

from pathlib import Path

from typing import Any, AsyncIterator, Awaitable, Callable, Dict
from datetime import datetime, timezone

router = web.RouteTableDef()

# generic function used as decorator to handle json related errors
def handle_json_error(
        func: Callable[[web.Request], Awaitable[web.Response]]
) -> Callable[[web.Request], Awaitable[web.Response]]:
    async def handler(request: web.Request) -> web.Response:
        try:
            return await func(request)
        except asyncio.CancelledError:
            raise
        except Exception as ex:
            return web.json_response(
                {"status": "failed", "reason": str(ex)}, status=400
            )

    return handler

# health check api
@router.get("/")
async def root(request: web.Request) -> web.Response:
    return web.json_response({"name": "Welcome to the purchases server", "healthy": True})

# [POST] api to add new customer
@router.post("/api/v1/customer")
@handle_json_error
async def api_new_customer(request: web.Request) -> web.Response:
    post_data = await request.json()
    name = post_data["name"]
    address = post_data["address"]
    date_created = datetime.now(timezone.utc)
    db = request.config_dict["DB"]
    async with db.execute(
            "INSERT INTO customer (name, address, date_created) VALUES(?, ?, ?)",
            [name, address, date_created],
    ) as cursor:
        customer_id = cursor.lastrowid
    await db.commit()
    return web.json_response(
        {
            "status": "ok",
            "data": {
                "id": customer_id,
                "name": name,
                "address": address,
                "created_on": date_created.strftime("%b %d %Y %H:%M:%S"),
            },
        }
    )

def get_db_path() -> Path:
    here = Path.cwd()
    while not (here / ".git").exists():
        if here == here.parent:
            raise RuntimeError("Cannot find root github dir")
        here = here.parent

    return here / "db.sqlite3"


async def init_db(app: web.Application) -> AsyncIterator[None]:
    sqlite_db = get_db_path()
    db = await aiosqlite.connect(sqlite_db)
    db.row_factory = aiosqlite.Row
    app["DB"] = db
    yield
    await db.close()


async def init_app() -> web.Application:
    app = web.Application()
    app.add_routes(router)
    app.cleanup_ctx.append(init_db)
    return app


def try_make_db() -> None:
    sqlite_db = get_db_path()
    if sqlite_db.exists():
        return

    with sqlite3.connect(sqlite_db) as conn:
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            customer_id INTEGER NOT NULL,
            date_created TEXT NOT NULL,
            last_updated TEXT)
        """
        )
        cur.execute(
            """CREATE TABLE customer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            date_created TEXT NOT NULL)
        """
        )
        conn.commit()


try_make_db()

web.run_app(init_app())