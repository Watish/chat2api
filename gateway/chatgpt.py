import json
from urllib.parse import quote

import requests
from fastapi import Request
from fastapi.responses import HTMLResponse

from app import app, templates
from gateway.login import login_html
from utils.kv_utils import set_value_for_key
from utils.configs import callback_url

with open("templates/chatgpt_context.json", "r", encoding="utf-8") as f:
    chatgpt_context = json.load(f)


@app.get("/", response_class=HTMLResponse)
async def chatgpt_html(request: Request):
    token = request.query_params.get("token")
    if not token:
        token = request.cookies.get("token")

    if len(token) != 45 and not token.startswith("eyJhbGciOi"):
        token = quote(token)

    # 密码和令牌均不存在
    if not token:
        return await login_html(request)

    # 加入鉴权
    if callback_url is not None:
        authResp = requests.post(callback_url + "/auth/callback", json={
            token
        })
        if authResp.status_code != 200:
            return await login_html(request)
        authJson = json.loads(authResp.text)
        if authJson["code"] < 1:
            return await login_html(request)
        token = authJson.data.token

    user_remix_context = chatgpt_context.copy()
    set_value_for_key(user_remix_context, "user", {"id": "user-chatgpt"})
    set_value_for_key(user_remix_context, "accessToken", token)

    response = templates.TemplateResponse("chatgpt.html", {"request": request, "remix_context": user_remix_context})
    response.set_cookie("token", value=token, expires="Thu, 01 Jan 2099 00:00:00 GMT")
    return response
