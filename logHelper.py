import json
import requests_async as req_async

async def gravar_log(request, response):

    log = {
        "method": request.method,
        "url" : request.url,
        "response" : str(response[0])
    }

    try:
        await req_async.post("http://127.0.0.1:3000/log", json=log)
    except:
        print("Erro ao gravar log!")