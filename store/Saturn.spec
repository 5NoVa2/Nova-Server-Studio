# Build on Windows with the pinned Store requirements. One-folder permits Qt DLL replacement.
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules,copy_metadata
root=Path(SPECPATH).parent;app=root/'app'
datas=[(str(app/'qml'),'qml'),(str(app/'sounds'),'sounds'),(str(app/'Nova.ico'),'.'),(str(app/'vps_setup.sh'),'.'),(str(root/'store/store-channel.json'),'.'),(str(root/'LICENSE'),'licenses/Saturn'),(str(root/'THIRD_PARTY_NOTICES.md'),'licenses/Saturn')]
for package in ['PySide6','PySide6_Essentials','PySide6_Addons','shiboken6','paramiko','cryptography','bcrypt','PyNaCl','cffi']:
 datas+=copy_metadata(package,recursive=False)
import sys
python_license=Path(sys.base_prefix)/'LICENSE.txt'
if python_license.exists():datas.append((str(python_license),'licenses/Python'))
hidden=['PySide6.QtCore','PySide6.QtGui','PySide6.QtWidgets','PySide6.QtQml','PySide6.QtQuick','PySide6.QtQuickControls2','PySide6.QtNetwork','PySide6.QtMultimedia','PySide6.QtSvg','paramiko']+collect_submodules('paramiko')
a=Analysis([str(root/'store/store_entry.py')],pathex=[str(app)],binaries=[],datas=datas,hiddenimports=hidden,excludes=['PyQt5','PyQt6','PySide2','PySide6.QtWebEngineCore','PySide6.QtWebEngineWidgets','PySide6.QtWebEngineQuick'],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='Saturn',debug=False,bootloader_ignore_signals=False,strip=False,upx=False,console=False,icon=str(app/'Nova.ico'))
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='Saturn')
