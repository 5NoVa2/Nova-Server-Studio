"""Per-Windows-user DPAPI protection for the remembered CurseForge key."""
import ctypes
import os
import tempfile
from pathlib import Path
from ctypes import wintypes

class Blob(ctypes.Structure):
    _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]

def _crypt(data, decrypt=False):
    if os.name!='nt':raise OSError('Saving API keys requires Windows account encryption.')
    crypt=ctypes.WinDLL('crypt32',use_last_error=True)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    buf=ctypes.create_string_buffer(data)
    source=Blob(len(data),ctypes.cast(buf,ctypes.POINTER(ctypes.c_ubyte)));out=Blob()
    kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree.restype=ctypes.c_void_p
    if decrypt:
        function=crypt.CryptUnprotectData
        function.argtypes=[ctypes.POINTER(Blob),ctypes.POINTER(wintypes.LPWSTR),ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
        description=None
    else:
        function=crypt.CryptProtectData
        function.argtypes=[ctypes.POINTER(Blob),wintypes.LPCWSTR,ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
        description='Saturn CurseForge API key'
    function.restype=wintypes.BOOL
    if not function(ctypes.byref(source),description,None,None,None,1,ctypes.byref(out)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:return ctypes.string_at(out.data,out.size)
    finally:kernel.LocalFree(ctypes.cast(out.data,ctypes.c_void_p))

class ApiKeyStore:
    def __init__(self,path):self.path=Path(path)
    def load(self):
        try:data=self.path.read_bytes()
        except FileNotFoundError:return ''
        return _crypt(data,decrypt=True).decode('utf-8')
    def save(self,key):
        if not key:
            self.path.unlink(missing_ok=True);return
        encrypted=_crypt(key.encode('utf-8'))
        self.path.parent.mkdir(parents=True,exist_ok=True)
        name=None
        try:
            with tempfile.NamedTemporaryFile(dir=self.path.parent,prefix='.nova-secret-',delete=False) as file:
                name=file.name;file.write(encrypted);file.flush();os.fsync(file.fileno())
            os.replace(name,self.path)
        finally:
            if name:Path(name).unlink(missing_ok=True)
