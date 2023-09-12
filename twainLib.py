# import asyncio
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
        self.sourceManager = twain.SourceManager(1, dsm_name=lib)  # dsm_name=lib

    def isScannerReady(self, device):
        if not self.sourceManager:
            self.start()
        try:
            self.scanner = self.sourceManager.OpenSource(self.sourceManager._encode(device))
            if self.scanner:
                self.scanner.close()
                return True
        except (twain.excTWCC_BUMMER, twain.excTWCC_PAPERJAM) as e:
            print(e)
            return False
        except Exception as e:
            print(e)
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

    def setScanArea(self, page="A4"):
        left = 0.000
        top = 0.000
        width = 8.267
        height = 11.693

        if page == "Letter":
            left = 0.000
            top = 0.000
            width = 8.500
            height = 11.000

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

    async def scan(self, callback, device=None, dpi=None, page=None):
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
        self.setScanArea(page)

        self.scanner.RequestAcquire(0, 1)
        info = self.scanner.GetImageInfo()
        try:
            self.handle = self.scanner.XferImageNatively()[0]
            image = twain.DIBToBMFile(self.handle)
            twain.GlobalHandleFree(self.handle)
            self.close()

            # check the folder exists
            if not os.path.exists("temp"):
                os.mkdir("temp", 0o777)

            img = Image.open(BytesIO(image))
            filename = str(time.time()) + '.jpg'
            img.save('temp/' + filename)
            await callback(filename)
            return True
        except Exception as e:
            print(e)
            return False

    async def multiscan(self, callback, device=None, dpi=None, page=None):
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
        self.setScanArea(page)

        try:

            self.scanner.RequestAcquire(0, 0)  # RequestAcquire(ShowUI, ShowModal)
            #self.scanner.GetImages(0, 0, callback, 'temp/')

        except Exception as e:
            print(e)

        while self.next():
            image = self.capture()
            if image:
                # check the folder exists
                # if not os.path.exists("temp"):
                #     os.mkdir("temp", 0o777)
                #
                # img = Image.open(BytesIO(image))
                # filename = str(time.time()) + '.jpg'
                # img.save('temp/' + filename)
                await callback(image)
            else:
                print("Capture didnt find any images")
                self.close()
                return True
        return True

    def next(self):
        try:
            print("next()")
            imagemin = self.scanner.GetImageInfo()
            print(imagemin)
            return True
        except (twain.excTWCC_PAPERJAM, twain.excTWCC_SEQERROR, twain.excTWCC_NODS) as e:
            self.closeScanner()
            print("next fired an exception")
            return False

    def capture(self):
        try:
            print("capture()")
            (handle, more_to_come) = self.scanner.XferImageNatively()
            if not os.path.exists("temp"):
                os.mkdir("temp", 0o777)
            bmp_filename = str(time.time()) + '.bmp'
            filename = str(time.time()) + '.jpg'
            twain.DIBToBMFile(handle, 'temp/'+bmp_filename)
            Image.open('temp/'+bmp_filename).save('temp/'+filename, format='JPEG')
            os.remove('temp/'+bmp_filename)
            return filename
        except twain.excDSTransferCancelled:
            return None

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
