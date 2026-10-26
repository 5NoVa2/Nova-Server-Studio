"""Render the real Friends tab with an isolated, stopped sample profile."""
import os,sys,tempfile,json
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE','Basic')
os.environ.setdefault('QT_QUICK_BACKEND','software')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from PySide6.QtWidgets import QApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject,QUrl,QPointF,Qt
from PySide6.QtTest import QTest
import shiboken6,qt_app
from hosts import HostManager

app=QApplication([])
with tempfile.TemporaryDirectory() as temp:
 qt_app.CACHE=Path(temp)/'cache';manager=HostManager(app,qt_app.Bridge);manager.renameProfile('Friends preview')
 manager.active.addFriend('Alex','Java');manager.active.addFriend('Bedrock Friend','Bedrock')
 engine=QQmlApplicationEngine();engine.rootContext().setContextProperty('nova',manager)
 engine.load(QUrl.fromLocalFile(str(Path(__file__).resolve().parents[1]/'app/qml/Main.qml')))
 assert engine.rootObjects()
 window=engine.rootObjects()[0];window.setWidth(1260);window.setHeight(850);window.findChild(QObject,'startupScene').finish();window.setProperty('page',5);QTest.qWait(400)
 tab=window.findChild(QObject,'friendsTab')
 QTest.mouseClick(window,Qt.LeftButton,Qt.NoModifier,tab.mapToScene(QPointF(tab.width()/2,tab.height()/2)).toPoint());QTest.qWait(300)
 assert window.findChild(QObject,'playerSections').property('currentIndex')==1
 output=Path('dist/preview');output.mkdir(parents=True,exist_ok=True)
 assert window.grabWindow().save(str(output/'Saturn-Friends.png'))
 (output/'friends-check.json').write_text(json.dumps({'friends':manager.active.friend_rows(),'live_server':False,'page':5,'tab':'Friends'},indent=2))
 shiboken6.delete(engine);manager.queue.timer.stop()
 for session in manager.sessions.values():session.timer.stop();session.api_save_timer.stop()
