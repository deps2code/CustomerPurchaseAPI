import asyncio
import sqlite3
import aiosqlite
from aiohttp import web

from pathlib import Path

from typing import Any, AsyncIterator, Dict
from datetime import datetime, timezone

from middlewares import setup_middlewares
from models import Purchase

router = web.RouteTableDef()


# health check api
@router.get("/")
async def root(request: web.Request) -> web.Response:
    return web.json_response({"name": "Welcome to the purchases server", "healthy": True})


# [POST] api to add new customer
@router.post("/api/v1/customer")
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


# [POST] api to add new customer purchase
@router.post("/api/v1/purchase/{customer_id}")
async def api_new_purchase(request: web.Request) -> web.Response:
    status = "ok"
    post_data = await request.json()
    purchase_name = post_data["purchase_name"]
    quantity = post_data["quantity"]
    customer_id = request.match_info["customer_id"]
    purchased_on = datetime.now(timezone.utc)
    db = request.config_dict["DB"]

    async with db.execute("SELECT count(*) as count FROM customer where id = ?",
                          [request.match_info["customer_id"]]) as cursor:
        async for row in cursor:
            if row["count"] < 1:
                status = "failed"
    await db.commit()
    if status == "failed":
        return web.json_response({"status": status, "data": "Customer doesn't exist"})
    else:
        if quantity <= 0:
            return web.json_response({"status": status, "data": "Quantity can't be less than 1"})
        async with db.execute(
                "INSERT INTO purchases (purchase_name, quantity, date_created, customer_id) VALUES(?, ?, ?, ?)",
                [purchase_name, quantity, purchased_on, customer_id],
        ) as cursor:
            purchase_id = cursor.lastrowid
        await db.commit()
        return web.json_response(
            {
                "status": status,
                "data": {
                    "id": purchase_id,
                    "purchase_name": purchase_name,
                    "quantity": quantity,
                    "customer_id": customer_id,
                    "purchased_on": purchased_on.strftime("%b %d %Y %H:%M:%S"),
                },
            }
        )


# [GET] api to list customer purchases
@router.get("/api/v1/purchase/{customer_id}")
async def api_list_purchase(request: web.Request) -> web.Response:
    response = []
    status = "ok"
    db = request.config_dict["DB"]
    async with db.execute("SELECT count(*) as count FROM customer where id = ?",
                          [request.match_info["customer_id"]]) as cursor:
        async for row in cursor:
            if row["count"] < 1:
                status = "failed"
    await db.commit()
    if status == "failed":
        return web.json_response({"status": status, "data": "Customer doesn't exist"})
    else:
        async with db.execute("SELECT id, purchase_name, quantity, date_created, last_updated FROM purchases "
                              "where customer_id = ?", [request.match_info["customer_id"]]) as cursor:
            async for row in cursor:
                response.append(
                    {
                        "purchase_id": row["id"],
                        "purchase_name": row["purchase_name"],
                        "quantity": row["quantity"],
                        "purchased_on": row["date_created"],
                        "last_updated_on": row["last_updated"]
                    }
                )
        return web.json_response({"status": status, "data": response})


# [DELETE] api to remove customer purchases
@router.delete("/api/v1/purchase/{customer_id}")
async def api_del_purchase(request: web.Request) -> web.Response:
    customer_id = request.match_info["customer_id"]
    req_data = await request.json()
    purchase_ids = req_data["purchase_ids"]
    is_delete_all = req_data["delete_all"]
    db = request.config_dict["DB"]

    if is_delete_all:
        async with db.execute("DELETE FROM purchases WHERE customer_id = ?", [customer_id]) as cursor:
            deleted_count = cursor.rowcount
    else:
        async with db.execute("DELETE FROM purchases WHERE customer_id = ? and id IN ({seq})".
                                      format(seq=",".join(["?"] * len(purchase_ids))),
                              [customer_id, *purchase_ids]) as cursor:
            deleted_count = cursor.rowcount

    await db.commit()
    return web.json_response({"status": "ok", "deleted_count": deleted_count})


# [PATCH] api to update customer purchase
@router.patch("/api/v1/purchase/{purchase_id}")
async def api_update_purchase(request: web.Request) -> web.Response:
    purchase_id = request.match_info["purchase_id"]
    patch_data = await request.json()
    purchase_name = patch_data["purchase_name"]
    quantity = patch_data["quantity"]

    db = request.config_dict["DB"]
    fields = {}
    if "purchase_name" in patch_data:
        fields["purchase_name"] = purchase_name
    if "quantity" in patch_data:
        fields["quantity"] = quantity
    fields["last_updated"] = datetime.now(timezone.utc)

    if fields:
        field_names = ", ".join(f"{name} = ?" for name in fields)
        field_values = list(fields.values())
        await db.execute(
            f"UPDATE purchases SET {field_names} WHERE id = ?", field_values + [purchase_id]
        )
        await db.commit()

    new_purchase = Purchase(purchase_id)
    new_purchase_data = await new_purchase.fetch_purchase_from_db(db, purchase_id)
    return web.json_response(
        {
            "status": "ok",
            "data": {
                "id": new_purchase_data["id"],
                "purchase_name": new_purchase_data["name"],
                "quantity": new_purchase_data["quantity"],
                "purchased_on": new_purchase_data["date_created"],
                "last_updated_on": new_purchase_data["last_updated"],
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
    setup_middlewares(app)
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