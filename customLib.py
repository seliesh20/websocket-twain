import os
import platform

def is_windows_32():
    return platform.architecture().__contains__("32bit")and platform.architecture().__contains__("WindowsPE")

def is_windows_64():
    return platform.architecture().__contains__("64bit")and platform.architecture().__contains__("WindowsPE")

def load_twain_dll():
    #print(os.environ["PATH"])
    if (is_windows_32()):
        lib = "C:\\Windows\\twain_32.dll"
        return lib
    if (is_windows_64()):
        lib = "C:\\Windows\\twaindsm.dll"
        return lib
    return None


