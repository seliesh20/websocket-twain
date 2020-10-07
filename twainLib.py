import asyncio
import os
import twain
import customLib
from PIL import Image
from io import BytesIO
import time

class twainLib(object):
    def __init__(self):
        self.scanner = None
        self.sourceManager = None
        self.dpi = 200
        self.scannedImages = {}

    def start(self):
        lib = customLib.load_twain_dll()
        self.sourceManager = twain.SourceManager(1, dsm_name=lib)

    def isScannerReady(self, device):
        if not self.sourceManager:
            self.start()
        try:
            self.scanner = self.sourceManager.OpenSource(self.sourceManager._encode(device))
            if self.scanner:
                self.scanner.close()
                return True
        except twain.excTWCC_BUMMER as e:
            print(e)
            return False
        finally:
            self.close()
        return False

    def getScanners(self):
        self.start()
        scanners = self.sourceManager.GetSourceList()
        return scanners

    def setScanner(self, device):
        try:
            if not self.sourceManager:
                self.start()
            self.scanner = self.sourceManager.OpenSource(self.sourceManager._encode(device))
        except twain.excDSOpenFailed as e:
            print(e)

    def setDPI(self, dpi):
        """Set DPI to selected scanner and dpi to self.dpi
        """
        try:
            self.dpi = int(dpi)
            self.scanner.SetCapability(
                twain.ICAP_XRESOLUTION, twain.TWTY_FIX32, self.dpi)
            self.scanner.SetCapability(
                twain.ICAP_YRESOLUTION, twain.TWTY_FIX32, self.dpi)
        except Exception as e:
            print(e)

    def setScanArea(self, left=0.0, top=0.0, width=8.267, height=11.693):
        width = float(width)
        height = float(height)
        left = float(left)
        top = float(top)
        try:
            self.scanner.SetImageLayout((left, top, width, height), 1, 1, 1)
        except Exception as e:
            print(e)

    def setPixelType(self, pixelType):
        """Set pixelType to selected scanner

        Args:
        pixelType: String  bw / gray / color
        """
        try:
            pixelTypeMap = {'bw': twain.TWPT_BW,
                            'gray': twain.TWPT_GRAY,
                            'color': twain.TWPT_RGB}
            try:
                pixelType = pixelTypeMap[pixelType]
            except:
                pixelType = twain.TWPT_RGB
            self.scanner.SetCapability(
                twain.ICAP_PIXELTYPE, twain.TWTY_UINT16, pixelType)
        except Exception as e:
            print(e)

    async def scan(self, callback, device=None, dpi=None):
        if not self.sourceManager:
            self.start()
        devices = self.getScanners()
        if device:
            self.setScanner(device)
        else:
            self.setScanner(devices[0])
        print(self.scanner)

        if dpi:
           self.setDPI(dpi)

        self.setPixelType("color")
        self.setScanArea()

        self.scanner.RequestAcquire(0, 1)
        info = self.scanner.GetImageInfo()
        try:
            self.handle = self.scanner.XferImageNatively()[0]
            image = twain.DIBToBMFile(self.handle)
            twain.GlobalHandleFree(self.handle)
            self.close()

            #check the folder exists
            if not os.path.exists("temp"):
                os.mkdir("temp", 0o777)

            img = Image.open(BytesIO(image))
            filename = str(time.time())+'.jpg'
            img.save('temp/'+filename)
            await callback(filename)
            return True
        except Exception as e:
            print(e)
            return False

    async def multiscan(self, callback, device=None, dpi=None):
        if not self.sourceManager:
            self.start()
        devices = self.getScanners()

        if device:
            self.setScanner(device)
        else:
            self.setScanner(devices[0])

        if dpi:
           self.setDPI(dpi)

        self.setPixelType("color")
        self.setScanArea()

        try:
            self.scanner.RequestAcquire(0, 0)  # RequestAcquire(ShowUI, ShowModal)
        except Exception as e:
            print(e)

        while self.next():
            image = self.capture()
            if image:
                # check the folder exists
                if not os.path.exists("temp"):
                    os.mkdir("temp", 0o777)

                img = Image.open(BytesIO(image))
                filename = str(time.time()) + '.jpg'
                img.save('temp/' + filename)
                await callback(filename)
            else:
                print("Capture didnt find any images")
        return True

    def next(self):
        try:
            print("next()")
            self.scanner.GetImageInfo()
            print("image_info()")
            return True
        except twain.excTWCC_SEQERROR:
            self.closeScanner()
            print("next fired an exception")
            return False

    def capture(self):
        try:
            print("capture()")
            (handle, more_to_come) = self.scanner.XferImageNatively()
        except twain.excDSTransferCancelled:
            self.close()
            return None
        image = twain.DIBToBMFile(handle)
        twain.GlobalHandleFree(handle)
        return image

    def closeScanner(self):
        if self.scanner:
            self.scanner.destroy()
        self.scanner = None

    def close(self):
        if self.scanner:
            self.scanner.destroy()
        if self.sourceManager:
            self.sourceManager.destroy()
        (self.scanner, self.sourceManager) = (None, None)

    def __del__(self):
        self.close()
