import sqlite3
from pathlib import Path

from typing import AsyncIterator

import aiosqlite
from aiohttp import web

router = web.RouteTableDef()

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