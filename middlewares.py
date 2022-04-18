import asyncio

from aiohttp import web

@web.middleware
async def error_middleware(request, handler):
    try:
        return await handler(request)
    except asyncio.CancelledError:
        raise
    except Exception as ex:
        return web.json_response(
            {"status": "failed", "reason": str(ex)}, status=400
        )


def setup_middlewares(app):
    app.middlewares.append(error_middleware)