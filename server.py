import os
import aiohttp
from aiohttp import web
import toml
import yarl

with open("server-config.toml") as f:
    config = toml.loads(f.read())

OAUTH_URL = f"https://slack.com/oauth/v2/authorize?client_id={config['client-id']}&scope=channels:history,reactions:write&user_scope="

async def route(request: web.Request) -> web.Response:
    code = request.query.get("code")
    if not code:
        raise web.HTTPTemporaryRedirect(OAUTH_URL) # redirect back to the oauth url, which will direct back to here with the temp token
    
    async with aiohttp.ClientSession() as session:
        url = yarl.URL("https://api.slack.com/api/oauth.v2.access").with_query({
            "client_id": config["client-id"],
            "client_secret": config["client-secret"],
            "code": code,
            "grant_type": "authorization_code"
        })

        async with session.post(url) as resp: # exchange temp token for access token
            if resp.status != 200:
                return web.Response(body=f"slack error: {await resp.text()}", status=500) # lazy cop out en lieu of actual error handling...
            
            data = await resp.json()
            if not data["ok"]:
                return web.Response(body=f"slack error: {data}", status=500)
            
            team = data["team"]["name"]
            token = data["access_token"]

            with open("tokens.txt", mode="a") as f:
                f.write(f"{team}: {token}\n")
            
            with open(".live-token", "w") as f: # janky but its fine
                f.write(token)
            
            app["token"] = token
    
    return web.Response(body=f"Access token for {team} is: {token}", status=200)

async def fetcher_route(request: web.Request) -> web.Response:
    auth = request.headers.get("Authorization")
    if not auth or auth != config["simpleauth-pass"]:
        return web.Response(status=401)

    if not app["token"]:
        return web.Response(status=400, body=OAUTH_URL)
    
    payload = {
        "app-token": config['app-token'],
        "bot-token": app['token'],
    }
    
    return web.json_response(payload)

app = web.Application()
app["token"] = None

if os.path.exists(".live-token"): # le jank
    with open(".live-token") as __f:
        app["token"] = __f.read().strip()

    del __f

app.router.add_get("/vk/oauth", route)
app.router.add_get("/vk/fetch", fetcher_route)

web.run_app(app, port=config["port"]) # proxied via nginx for TLS (required for oauth, unless the server is on 127.0.0.1)