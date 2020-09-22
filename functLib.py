import base64
import io
import os
import time

from fpdf import FPDF
import twainLib
import asyncio
from PIL import Image

twainObject = twainLib.twainLib()

class functLib:

    async def getScanners(self, sendCallback, websocket):
        send_data = {}
        send_data["action"] = "getScanners"
        send_data["scanners"] = twainObject.getScanners()
        print(send_data["scanners"])
        await sendCallback(send_data, websocket)

    def isValidScanner(self, params, sendCallback, websocket):
        scanners = twainObject.getScanners()
        return params['scanner'] in scanners

    async def scanSingle(self, params, sendCallback, websocket):
        (img_str, scanner, dpi) = (None, None, None)
        if params["scanner"]:
            scanner = params["scanner"]
        if params["dpi"]:
            dpi = params["dpi"]

        async def callback(img_str):
            send_data = {}
            send_data["action"] = "pageComplete"
            send_data["image"] = img_str
            with open('temp/'+img_str, "rb") as img_file:
                send_data["base64"] = base64.b64encode(img_file.read()).decode('utf-8')
            await sendCallback(send_data, websocket)

        try:
            # twainObject.scanDialog(scanner)
            await twainObject.scan(callback, scanner, dpi)
            print("Scan Completed")
        except Exception as e:
            print(e)

        send_data = {}
        send_data["action"] = "scanComplete"
        await sendCallback(send_data, websocket)

    async def scan(self, params, sendCallback, websocket):
        (img_str, scanner, dpi) = (None, None, None)
        if params["scanner"]:
            scanner = params["scanner"]
        if params["dpi"]:
            dpi = params["dpi"]

        async def callback(img_str):
            send_data = {}
            send_data["action"] = "pageComplete"
            send_data["image"] = img_str
            with open('temp/'+img_str, "rb") as img_file:
                send_data["base64"] = base64.b64encode(img_file.read()).decode('utf-8')
            await sendCallback(send_data, websocket)

        try:
            # twainObject.scanDialog(scanner)
            await twainObject.multiscan(callback, scanner, dpi)
        except Exception as e:
            print(e)

        send_data = {}
        send_data["action"] = "scanComplete"
        await sendCallback(send_data, websocket)

    async def createPdf(self, params, sendCallback, websocket):
        '''
        Combine Images into PDF and send the link to application
        :param params: URI parameters
        :param sendCallback: Callback for sending result json to application
        :param websocket: Websocket object of the connection
        :return:
        '''

        if params["files"]:
            cover = Image.open('temp/'+params["files"]["0"])
            width, height = cover.size
            cover.close()

            pdf = FPDF(unit="pt", format=[width, height])

            for key in params["files"]:
                pdf.add_page()
                pdf.image('temp/'+params["files"][key], 0, 0)

            filename = str(time.time())+'.pdf'
            pdf.output('temp/'+filename, "F")
            pdf.close()

            #Remove the files
            for key in params["files"]:
                os.remove('temp/' + params["files"][key])

            send_data = {}
            send_data["action"] = "documentCreated"
            send_data["filename"] = filename
            send_data["base64"] = "data:application/pdf;base64,"+base64.b64encode(open('temp/'+filename, "rb").read()).decode('utf-8')
            await sendCallback(send_data, websocket)

