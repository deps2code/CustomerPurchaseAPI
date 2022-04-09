import pytest
from aiohttp import web

async def get_customer_purchases(request):
    if request.method == "POST":
        request.app['purchase_name'] = (await request.post())['purchase_name']
        request.app['quantity'] = (await request.post())['quantity']
        return web.json_response(
                {
                    "status": "ok",
                    "data": [
                        {
                            "purchase_name": request.app['purchase_name'],
                            "quantity": int(request.app['quantity'])
                        }
                    ]
                }
            )
    else:
        return web.json_response(
                {
                    "status": "ok",
                    "data": [
                        {
                            "purchase_id": 1,
                            "purchase_name": "Iphone 10 Pro",
                            "quantity": 4,
                            "purchased_on": "2022-04-09 12:43:22.237526+00:00"
                        }
                    ]
                }
            )


async def add_customer_purchases(request):
    return web.json_response(
            {
                "status": "ok",
                "data": [
                    {
                        "purchase_id": 1,
                        "purchase_name": "Iphone 10 Pro",
                        "quantity": 4,
                        "purchased_on": "2022-04-09 12:43:22.237526+00:00"
                    }
                ]
            }
        )

async def test_get_customer_purchases(aiohttp_client, loop):
    app = web.Application()
    app.router.add_get('/api/v1/purchase/1', get_customer_purchases)
    client = await aiohttp_client(app)
    resp = await client.get('/api/v1/purchase/1')
    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "ok"
    assert data["data"][0]["purchase_name"] == "Iphone 10 Pro"
    assert data["data"][0]["quantity"] == 4


async def test_add_customer_purchases(aiohttp_client, loop):
    app = web.Application()
    app.router.add_post('/api/v1/purchase/1', get_customer_purchases)
    client = await aiohttp_client(app)
    resp = await client.post('/api/v1/purchase/1', data={"purchase_name":"Iphone 13","quantity":2})
    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "ok"
    assert data["data"][0]["purchase_name"] == "Iphone 13"
    assert data["data"][0]["quantity"] == 2
