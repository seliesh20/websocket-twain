import json
import asyncio
import random

import websockets
import functLib
functObject = functLib.functLib()
DEFAULTSCANNER = "default"
DEFAULTDPI = 200

async def sendToUser(send_data, websocket):
    try:
        if(websocket.open):
            await websocket.send(json.dumps(send_data))
    except Exception as e:
        print(e)


async def serverConfig(websocket, path):
    global DEFAULTSCANNER
    global DEFAULTDPI
    while True:

        if (websocket.open):
            action_params = json.loads(await websocket.recv())
            (action, params) = (None, {})

            if "action" in action_params.keys():
                action = action_params["action"]

            if "params" in action_params.keys():
                params = action_params["params"]

            if (action == 'getScanners'):
                await functObject.getScanners(sendToUser, websocket)
            if (action == 'getScanner'):
                params["scanner"] = DEFAULTSCANNER
                isvalid = functObject.isValidScanner(params, sendToUser, websocket)
                send_data = {}
                send_data["action"] = action
                if isvalid:
                    send_data["scanner"] = DEFAULTSCANNER
                    send_data["dpi"] = DEFAULTDPI
                    await sendToUser(send_data, websocket)
                else:
                    send_data["scanner"] = "false"
                    await sendToUser(send_data, websocket)

            if (action == 'setScanner'):
                isvalid = functObject.isValidScanner(params, sendToUser, websocket)
                send_data = {}
                send_data["action"] = action
                if isvalid:
                    DEFAULTSCANNER = params["scanner"]
                    DEFAULTDPI = params["dpi"]
                    send_data["status"] = "true"
                    send_data["scanner"] = params["scanner"]
                    await sendToUser(send_data, websocket)
                else:
                    send_data["status"] = "false"
                    await sendToUser(send_data, websocket)

            if (action == 'scanSingle'):
                await functObject.scanSingle(params, sendToUser, websocket)
            if (action == 'scan'):
                await functObject.scan(params, sendToUser, websocket)
            if (action == 'createDocument'):
                await functObject.createPdf(params, sendToUser, websocket)
            if (action == 'removeFiles'):
                await functObject.removeFiles(params, sendToUser, websocket)

        await asyncio.sleep(random.random() * 3)

start_server = websockets.server.serve(serverConfig, 'localhost', 8087)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
