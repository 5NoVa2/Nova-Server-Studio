import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: win
    visible: true; width: 1260; height: 850; minimumWidth: 1040; minimumHeight: 700
    title: 'Saturn | Server Launcher'; color: '#090b10'
    property var s: nova.state
    property int page: 0
    property int shownProfileIndex: 0
    property var fileRows: []
    property string fileSignature: ''
    function syncFileRows() { const rows=s.browserRows || []; const signature=JSON.stringify([s.browserRoot,s.browserPath,rows]); if(signature!==fileSignature) { fileSignature=signature; fileRows=rows; browserList.currentIndex=-1 } }
    property var serverRows: []
    property string serverSignature: ''
    function syncServers() { const rows=s.profileItems || []; const signature=JSON.stringify(rows); if(signature!==serverSignature) { serverSignature=signature; serverRows=rows } }
    property alias uiSounds: uiAudio
    UiSounds { id: uiAudio; soundsEnabled: s.sound_enabled!==false; masterVolume: s.sound_volume===undefined ? 0.3 : s.sound_volume; interactive: win.visible && !intro.active && !s.exiting }
    property bool full: false
    property var titles: ['Dashboard','Server','Modpacks','Files','Settings','Players','Tasks','Help']
    property var navigation: [{label:'Dashboard',page:0,icon:'◈'},{label:'Server',page:1,icon:'▷'},{label:'Files',page:3,icon:'≡'},{label:'Tasks',page:6,icon:'☷'},{label:'Players',page:5,icon:'♙'},{label:'Settings',page:4,icon:'⚙'},{label:'Help',page:7,icon:'?'}]
    property bool showPackApi: false
    property bool serverReleasesOnly: true
    function packReleases() { return (s.releases || []).map((row,index)=>({row:row,index:index})).filter(item=>!serverReleasesOnly || item.row.serverPackFileId) }

    property color muted: '#8e96a8'
    font.family: 'Segoe UI'
    onClosing: function(close) { close.accepted=false; nova.action('tray') }
    Component.onCompleted: { shownProfileIndex=s.profileIndex || 0; syncServers(); syncFileRows(); intro.begin() }
    function selectDashboardServer(index) { nova.selectProfile(index) }
    function fullscreen() { full=!full; if(full) showFullScreen(); else showNormal() }
    Shortcut { sequence: 'F11'; onActivated: win.fullscreen() }
    Shortcut { sequence: 'Escape'; onActivated: { if(intro.active) intro.finish(); else if(win.full) win.fullscreen() } }
    Shortcut { sequence: 'Ctrl+S'; onActivated: nova.action('save_all') }
    function cpuText(value) { return value===null || value===undefined ? '—' : Number(value).toFixed(1)+'%' }
    function ramText(value) { return value===null || value===undefined ? '—' : (Number(value)/1073741824).toFixed(2)+' GB' }
    component Caption: Text { color: win.muted; font.pixelSize: 12; font.letterSpacing: 1.3 }
    component Heading: Text { color: '#f0f1f7'; font.pixelSize: 29; font.weight: Font.DemiBold }
    component Body: Text { color: '#a4adbe'; font.pixelSize: 13; wrapMode: Text.WordWrap }
    component Action: NButton { motion: !s.reduced; enabled: !s.exiting }
    component Field: NField { enabled: !s.exiting }
    component Combo: NCombo { enabled: !s.busy && !s.exiting }
    component SoundSwitch: Switch {
        id: soundSwitch
        hoverEnabled: true
        onHoveredChanged: if(hovered && enabled) uiAudio.play('hover')
        Connections { target: soundSwitch; function onToggled() { uiAudio.play('click') } }
    }
    component BusyAction: Action { enabled: !s.busy && !s.exiting }
    component SettingsSection: Panel {
        id: section
        property string title
        property bool expanded: false
        default property alias content: sectionBody.data
        Layout.fillWidth: true
        implicitHeight: sectionLayout.implicitHeight+40
        ColumnLayout {
            id: sectionLayout; anchors.fill: parent; anchors.margins: 20; spacing: 12
            Action { objectName: section.objectName+'Toggle'; text: section.title+(section.expanded ? '   −' : '   +'); Layout.fillWidth: true; onClicked: { section.expanded=!section.expanded; uiAudio.play('transition') } }
            ColumnLayout { id: sectionBody; Layout.fillWidth: true; spacing: 12; visible: section.expanded }
        }
    }
    Rectangle { anchors.fill: parent; gradient: Gradient { GradientStop { position: 0; color: '#10141e' } GradientStop { position: 0.7; color: '#090b10' } } }
    SaturnMark { anchors.right: parent.right; anchors.bottom: parent.bottom; width: 600; height: 450; opacity: 0.07 }
    Item {
        anchors.fill: parent; clip: true
        Repeater {
            model: 18
            Rectangle {
                required property int index
                width: index%3===0 ? 74 : 3; height: width; radius: width/2
                x: (index*173+130)%win.width; y: (index*117+10)%win.height
                color: width===3 ? '#64718a' : 'transparent'; border.color: width===3 ? 'transparent' : '#202a3c'; opacity: 0.3
                SequentialAnimation on y { running: !s.reduced && win.visible; loops: Animation.Infinite; NumberAnimation { to: -90; duration: 22000+index*1800 } NumberAnimation { to: win.height+90; duration: 0 } }
            }
        }
    }
    RowLayout {
        id: appSurface; opacity: intro.active ? 0 : 1
        Behavior on opacity { NumberAnimation { duration: s.reduced ? 0 : 400 } }
        anchors.fill: parent; anchors.margins: 14; spacing: 10
        Rectangle {
            Layout.preferredWidth: 184; Layout.fillHeight: true; radius: 25; color: '#b8101319'; border.color: '#2c333d'
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 20; spacing: 10
                SaturnMark { Layout.alignment: Qt.AlignHCenter; Layout.preferredWidth: 132; Layout.preferredHeight: 96 }
                Text { text: 'S A T U R N'; color: '#f3f4fa'; font.pixelSize: 21; font.weight: Font.Bold; Layout.topMargin: 12 }
                Caption { text: 'SERVER LAUNCHER'; font.pixelSize: 9; Layout.bottomMargin: 20 }
                Repeater {
                    model: win.navigation
                    Action {
                        required property var modelData; required property int index
                        objectName: 'nav_'+modelData.label; text: modelData.icon+'  '+modelData.label
                        Layout.fillWidth: true; primary: win.page===modelData.page || (modelData.page===1 && win.page===2)
                        onClicked: win.page=modelData.page
                    }
                }
                Item { Layout.fillHeight: true }
                Caption { text: 'CREATED BY NOVA'; font.pixelSize: 9 }
                Action { text: 'Minimize to tray'; Layout.fillWidth: true; onClicked: nova.action('tray') }
                Action { text: 'Exit Saturn'; danger: true; Layout.fillWidth: true; onClicked: nova.action('exit') }
            }
        }
        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; spacing: 0
            RowLayout {
                Layout.fillWidth: true; Layout.margins: 26; spacing: 14
                Caption { text: win.page===0 ? 'YOUR WORLD. YOUR RULES.' : (win.page===2 ? 'SERVER / MODPACKS' : win.titles[win.page].toUpperCase()); Layout.fillWidth: true }
                Rectangle { width: 7; height: 7; radius: 4; color: s.server==='Ready' ? '#9ee2bd' : s.server==='Starting' ? '#e8cc95' : '#666e7e' }
                Text { text: s.server; color: '#b9c1cf'; font.pixelSize: 12 }
                Text { text: '•  '+(s.use_vps===false ? 'Direct · no VPS' : s.tunnel); color: win.muted; font.pixelSize: 12 }
                Action { text: win.full ? 'Windowed' : 'Full screen'; implicitHeight: 34; onClicked: win.fullscreen() }
            }
            RowLayout {
                Layout.fillWidth: true; Layout.leftMargin: 26; Layout.rightMargin: 26; Layout.bottomMargin: 14; spacing: 10
                Combo { choices: (s.profileItems || [{name:'My server',status:s.server}]).map(p=>p.name+' · '+p.status); currentIndex: s.profileIndex || 0; Layout.fillWidth: true; onActivated: nova.selectProfile(currentIndex) }
                Field { id: profileName; placeholderText: 'New profile / rename'; Layout.preferredWidth: 170 }
                BusyAction { text: '+ Add'; implicitWidth: 72; onClicked: { nova.addProfile(profileName.text); profileName.clear() } }
                BusyAction { text: 'Rename'; implicitWidth: 80; onClicked: nova.renameProfile(profileName.text) }
                BusyAction { text: 'Remove'; implicitWidth: 80; danger: true; onClicked: nova.removeProfile() }
                Action { text: 'Stop all'; implicitWidth: 85; danger: true; onClicked: nova.action('stop_all') }
            }
            Rectangle {
                visible: !!s.error; Layout.fillWidth: true; Layout.leftMargin: 26; Layout.rightMargin: 26; Layout.bottomMargin: 12
                implicitHeight: errorRow.implicitHeight+24; radius: 14; color: '#362027'; border.color: '#69414d'
                RowLayout { id: errorRow; anchors.fill: parent; anchors.margins: 12
                    Text { text: s.error; color: '#ffc1cb'; wrapMode: Text.WordWrap; Layout.fillWidth: true; font.pixelSize: 13 }
                    Action { text: 'Dismiss'; onClicked: nova.action('dismiss') }
                }
            }
            TabBar { objectName: 'serverSections'; visible: win.page===1 || win.page===2; currentIndex: win.page===2 ? 1 : 0
                Layout.fillWidth: true; Layout.leftMargin: 26; Layout.rightMargin: 26; Layout.bottomMargin: 16
                background: Item {}
                NTab { objectName: 'serverControlTab'; text: 'Server controls'; onClicked: win.page=1 }
                NTab { objectName: 'serverModpacksTab'; text: 'Modpacks'; onClicked: win.page=2 }
            }
            StackLayout {
                id: pages; property real revealOffset: 0; transform: Translate { y: pages.revealOffset } currentIndex: win.page; Layout.fillWidth: true; Layout.fillHeight: true
                // DASHBOARD
                ScrollView { id: homeScroll; clip: true; contentWidth: availableWidth
                    ColumnLayout {
                        width: homeScroll.availableWidth-52; x: 26; spacing: 20
                        RowLayout { Layout.fillWidth: true
                            ColumnLayout { Layout.fillWidth: true; spacing: 8
                                Caption { text: 'WELCOME TO SATURN'; font.pixelSize: 10 }
                                Heading { text: 'Your next world starts here.'; font.pixelSize: 32 }
                                Body { text: 'One studio. Every server. Yours to shape.' }
                            }
                            Caption { text: (s.hostingCount || 0)+' ONLINE'; font.pixelSize: 10 }
                        }
                        Panel { Layout.fillWidth: true; implicitHeight: 266; clip: true
                            Image { anchors.fill: parent; source: (s.cf_pack || {}).artwork || ''; asynchronous: true; fillMode: Image.PreserveAspectCrop; opacity: 0.18 }
                            SaturnMark { anchors.right: parent.right; anchors.rightMargin: -24; anchors.verticalCenter: parent.verticalCenter; width: 360; height: 270; opacity: 0.4 }
                            RowLayout { anchors.fill: parent; anchors.margins: 28; spacing: 20
                                ColumnLayout { Layout.fillWidth: true; spacing: 12
                                    RowLayout { spacing: 8
                                        Rectangle { width: 7; height: 7; radius: 4; color: s.server==='Ready' ? '#acf1ce' : s.server==='Starting' ? '#f2cc91' : '#798594' }
                                        Caption { text: s.server.toUpperCase()+'  /  '+(s.installedEngine || s.engine).toUpperCase(); font.pixelSize: 10 }
                                    }
                                    Text { objectName: 'serverHeroName'; text: s.profileName || 'My server'; color: '#f5f6fa'; font.pixelSize: 35; font.weight: Font.Light; Layout.fillWidth: true; elide: Text.ElideRight }
                                    Body { text: (s.cf_pack.name || 'Minecraft '+s.version)+'  ·  '+(s.joinDisplay || 'localhost'); Layout.fillWidth: true; elide: Text.ElideRight; maximumLineCount: 1 }
                                    RowLayout { spacing: 24
                                        Column { spacing: 5; Text { text: (s.players || []).length; color: '#eef2f8'; font.pixelSize: 24 } Caption { text: 'PLAYERS'; font.pixelSize: 9 } }
                                        Column { spacing: 5; Text { text: s.uptime; color: '#eef2f8'; font.pixelSize: 24 } Caption { text: 'UPTIME'; font.pixelSize: 9 } }
                                        Column { spacing: 5; Text { text: s.use_vps===false ? 'Direct hosting' : s.tunnel; color: '#eef2f8'; font.pixelSize: 18 } Caption { text: s.use_vps===false ? 'CONNECTION MODE' : 'PUBLIC TUNNEL'; font.pixelSize: 9 } }
                                    }
                                    Item { Layout.fillHeight: true }
                                    RowLayout { spacing: 10
                                        BusyAction { text: s.server==='Stopped' ? '▷  Start hosting' : '□  Stop hosting'; primary: true; implicitWidth: 164; onClicked: nova.action(s.server==='Stopped' ? 'hosting' : 'stop') }
                                        BusyAction { text: 'Start local'; visible: s.server==='Stopped' && s.use_vps!==false; onClicked: nova.action('start') }
                                        Action { text: 'Copy address'; onClicked: nova.action('copy') }
                                        Action { text: 'Server setup  ↗'; onClicked: win.page=1 }
                                    }
                                }
                            }
                        }
                        Panel { Layout.fillWidth: true; implicitHeight: 134
                            ColumnLayout { anchors.fill: parent; anchors.margins: 20; spacing: 10
                                Caption { text: 'SERVER RESOURCES · '+(s.profileName || 'My server'); font.pixelSize: 10 }
                                RowLayout { Layout.fillWidth: true; spacing: 24
                                    ColumnLayout { Layout.fillWidth: true
                                        Text { objectName: 'serverCpuStat'; text: win.cpuText(s.cpuLoad); color: '#eef2f8'; font.pixelSize: 26 }
                                        Caption { text: 'CPU LOAD'; font.pixelSize: 9 }
                                    }
                                    ColumnLayout { Layout.fillWidth: true
                                        Text { objectName: 'serverRamStat'; text: win.ramText(s.ramBytes); color: '#eef2f8'; font.pixelSize: 26 }
                                        Caption { text: 'RAM IN USE'; font.pixelSize: 9 }
                                    }
                                    Body { text: s.server==='Stopped' ? 'Start this server to see live usage.' : 'Live · refreshes every 2 seconds'; Layout.fillWidth: true }
                                }
                                Body { text: 'Server process only · CPU is a share of total PC capacity · RAM is resident memory'; font.pixelSize: 11; Layout.fillWidth: true }
                            }
                        }
                        RowLayout { Layout.fillWidth: true
                            Caption { text: 'YOUR SERVERS'; font.pixelSize: 10; Layout.fillWidth: true }
                            Action { text: '+ New server'; implicitHeight: 34; onClicked: { profileName.forceActiveFocus(); profileName.selectAll() } }
                        }
                        ListView { id: serverCards; Layout.fillWidth: true; Layout.preferredHeight: 155; orientation: ListView.Horizontal; spacing: 14; clip: true; model: win.serverRows
                            delegate: Panel { required property var modelData; required property int index
                                width: 248; height: 145; y: cardHover.hovered ? 0 : 5
                                border.color: index===s.profileIndex ? '#8d9aaf' : cardHover.hovered ? '#626f80' : '#303741'
                                Behavior on y { NumberAnimation { duration: s.reduced ? 0 : 150; easing.type: Easing.OutCubic } }
                                Image { anchors.right: parent.right; anchors.margins: 16; anchors.verticalCenter: parent.verticalCenter; width: 74; height: 74; source: modelData.artwork || ''; asynchronous: true; fillMode: Image.PreserveAspectCrop; opacity: 0.25 }
                                Column { anchors.fill: parent; anchors.margins: 20; spacing: 12
                                    Caption { text: modelData.engine.toUpperCase(); font.pixelSize: 9 }
                                    Text { width: parent.width; text: modelData.name; color: '#edf1f7'; font.pixelSize: 18; elide: Text.ElideRight }
                                    Row { spacing: 7
                                        Rectangle { y: 4; width: 6; height: 6; radius: 3; color: modelData.running ? '#acf1ce' : '#697485' }
                                        Text { text: (modelData.running ? 'Running' : 'Stopped')+'  ·  '+modelData.players+' players'; color: '#98a5b7'; font.pixelSize: 11 }
                                    }
                                }
                                HoverHandler { id: cardHover; onHoveredChanged: if(hovered) uiAudio.play('hover') }
                                TapHandler { onTapped: { uiAudio.play('click'); win.selectDashboardServer(index) } }
                            }
                        }
                        RowLayout { Layout.fillWidth: true; spacing: 14
                            Repeater { model: [{title:'Discover modpacks',sub:'Find your next adventure',icon:'▦',page:2},{title:'Files & backups',sub:'Make the world your own',icon:'≡',page:3},{title:'Your studio',sub:'Connections, ports & updates',icon:'⚙',page:4}]
                                Panel { required property var modelData; Layout.fillWidth: true; implicitHeight: 105
                                    border.color: quickHover.hovered ? '#78899f' : '#303741'
                                    RowLayout { anchors.fill: parent; anchors.margins: 20; spacing: 15
                                        Text { text: modelData.icon; color: '#c4cfdf'; font.pixelSize: 28 }
                                        ColumnLayout { Layout.fillWidth: true; spacing: 6
                                            Text { text: modelData.title; color: '#e6ecf6'; font.pixelSize: 14 }
                                            Body { text: modelData.sub; font.pixelSize: 11; Layout.fillWidth: true }
                                        }
                                    }
                                    HoverHandler { id: quickHover; onHoveredChanged: if(hovered) uiAudio.play('hover') }
                                    TapHandler { onTapped: { uiAudio.play('click'); win.page=modelData.page } }
                                }
                            }
                        }
                        Item { implicitHeight: 12 }
                    }
                }
                // SERVER
                ScrollView {
                    id: serverScroll; clip: true; contentWidth: availableWidth
                    ColumnLayout {
                        width: serverScroll.availableWidth-52; x: 26; spacing: 18
                        Heading { text: (s.profileName || 'Your server')+', at a glance.'; Layout.fillWidth: true; elide: Text.ElideRight }
                        RowLayout { Layout.fillWidth: true; spacing: 12
                            Repeater { model: [{label:'SERVER',value:s.server},{label:s.use_vps===false ? 'CONNECTION' : 'TUNNEL',value:s.use_vps===false ? 'Direct · no VPS' : s.tunnel},{label:'UPTIME',value:s.uptime},{label:'CPU',value:win.cpuText(s.cpuLoad)},{label:'RAM',value:win.ramText(s.ramBytes)}]
                                Panel { required property var modelData; Layout.fillWidth: true; implicitHeight: 100
                                    Column { anchors.fill: parent; anchors.margins: 20; spacing: 10
                                        Caption { text: modelData.label }
                                        Text { text: modelData.value; color: '#f3f5fc'; font.pixelSize: 21 }
                                    }
                                }
                            }
                        }
                        RowLayout { spacing: 10
                            BusyAction { text: 'Start hosting'; primary: true; onClicked: nova.action('hosting') }
                            BusyAction { text: 'Start local'; visible: s.use_vps!==false; onClicked: nova.action('start') }
                            BusyAction { text: 'Connect tunnel'; visible: s.use_vps!==false; onClicked: nova.action('tunnel') }
                            Action { text: 'Stop hosting'; danger: true; onClicked: nova.action('stop') }
                            Action { text: 'Copy address'; onClicked: nova.action('copy') }
                            Action { text: 'Players'; onClicked: win.page=5 }
                        }
                        Panel { Layout.fillWidth: true; implicitHeight: installColumn.implicitHeight+40
                            ColumnLayout { id: installColumn; anchors.fill: parent; anchors.margins: 20; spacing: 12
                                RowLayout { Layout.fillWidth: true
                                    Text { text: 'Prepare a world'; color: '#eef1fa'; font.pixelSize: 20; Layout.fillWidth: true }
                                    Body { text: s.cf_pack.name || 'Choose your server software' }
                                    BusyAction { objectName: 'browseModpacksButton'; text: 'Browse modpacks'; onClicked: packBrowserPopup.open() }
                                }
                                RowLayout {
                                    Combo { choices: ['Vanilla','Paper','Spigot','Forge','CurseForge','Bedrock']; currentIndex: choices.indexOf(s.engine); onActivated: { nova.update('engine',currentText); nova.action('versions') } }
                                    Combo { id: version; objectName: 'versionSelector'; popup.onOpened: nova.action('ensure_versions'); editable: true; choices: s.versions; displayText: s.version; editText: s.version; onActivated: nova.update('version',currentText); onAccepted: nova.update('version',editText); onEditTextChanged: { if(activeFocus) nova.draft('version',editText) } }
                                    BusyAction { text: 'Refresh versions'; onClicked: nova.action('versions') }
                                    Caption { text: 'RAM GB' }
                                    SpinBox { palette.base: '#151a23'; from: 2; to: 16; value: s.ram; onValueModified: nova.update('ram',value); enabled: s.engine!=='Bedrock'; palette.text: '#eeeeef'; palette.buttonText: '#eeeeef'; palette.button: '#303642' }
                                }
                                RowLayout { Layout.fillWidth: true
                                    Field { text: s.folder; placeholderText: 'Server folder'; Layout.fillWidth: true; onTextEdited: nova.draft('folder',text); onEditingFinished: nova.update('folder',text); objectName: 'folderField' }
                                    BusyAction { text: 'Browse'; onClicked: nova.browse('folder') }
                                    Field { visible: s.engine==='Forge'; text: s.loader; placeholderText: 'Forge build'; onTextEdited: nova.draft('loader',text); onEditingFinished: nova.update('loader',text) }
                                }
                                RowLayout {
                                    CheckBox { palette.base: '#242c3c'; palette.text: '#d8e2f6'; checked: !!s.agreed; text: 'I accept the Minecraft EULA'; palette.windowText: '#c0c8d8'; onToggled: nova.agree(checked) }
                                    Action { text: 'Read EULA'; onClicked: Qt.openUrlExternally('https://www.minecraft.net/eula') }
                                    BusyAction { text: 'Install / switch'; primary: true; onClicked: nova.action('install') }
                                    BusyAction { text: 'Manual backup'; onClicked: nova.action('backup') }
                                }
                                CheckBox { objectName: 'serverUseVpsToggle'; text: 'Use VPS tunnel'; checked: s.use_vps!==false; enabled: s.server==='Stopped' && s.tunnel==='Disconnected' && !s.busy; palette.windowText: '#c0c8d8'; onToggled: nova.update('use_vps',checked) }
                                Body { visible: s.use_vps===false; text: 'Direct hosting: no VPS or SSH needed. Forward your router’s public game port to this PC’s LAN IP and local game port. Java listens on your network interfaces; players use your public IP or domain. See Settings → Hosting connection for setup.'; Layout.fillWidth: true }
                                RowLayout { visible: s.use_vps!==false
                                    Caption { text: 'TUNNEL EDITION' }
                                    Combo { choices: ['Auto','Java','Bedrock']; currentIndex: choices.indexOf(s.tunnel_type || 'Auto'); onActivated: nova.update('tunnel_type',currentText) }
                                    Body { text: 'Java = TCP · Bedrock = UDP. Select the matching server edition.'; Layout.fillWidth: true }
                                }
                                Body { text: 'Switching replaces the whole folder. Create a backup first if you need to keep it. Manage backup schedules in Tasks.'; Layout.fillWidth: true }
                            }
                        }
                        Panel { Layout.fillWidth: true; implicitHeight: 310
                            ColumnLayout { anchors.fill: parent; anchors.margins: 18; spacing: 10
                                RowLayout { Caption { text: 'LIVE CONSOLE'; Layout.fillWidth: true } Action { text: 'Clear'; implicitHeight: 30; onClicked: nova.action('clear') } }
                                ScrollView { Layout.fillWidth: true; Layout.fillHeight: true; clip: true
                                    TextArea { text: s.logs; readOnly: true; selectByMouse: true; color: '#adbcd1'; font.family: 'Consolas'; font.pixelSize: 12; wrapMode: TextEdit.Wrap; background: null; onTextChanged: cursorPosition=length }
                                }
                                RowLayout { Layout.fillWidth: true
                                    Field { id: command; placeholderText: 'Server command — list, whitelist add, op…'; Layout.fillWidth: true; onAccepted: { nova.command(text); clear() } }
                                    Action { text: 'Send'; onClicked: { nova.command(command.text); command.clear() } }
                                }
                            }
                        }
                        Item { implicitHeight: 20 }
                    }
                }
                // Embedded Server / Modpacks browser; the popup shares this component.
                Loader { objectName: 'serverPackBrowser'; active: win.page===2 && !packBrowserPopup.visible; sourceComponent: packBrowserComponent }
                // FILES
                Item { ColumnLayout {
                    anchors.fill: parent; anchors.margins: 26; spacing: 14
                    RowLayout { Heading { text: 'Shape your world.'; Layout.fillWidth: true } BusyAction { text: 'Save All'; primary: true; enabled: s.filesLoaded && s.server==='Stopped' && !s.busy; onClicked: nova.action('save_all') } BusyAction { text: 'Reload files'; onClicked: nova.action('files') } }
                    Body { text: 'Core server files load automatically. New installations are saved and ready; Save All or Ctrl+S saves your file and server settings edits.'; Layout.fillWidth: true }
                    Body { visible: !s.filesLoaded; text: 'Install a server or choose its folder on Server to load editable settings.'; Layout.fillWidth: true }
                    TabBar { id: fileTabs; onCurrentIndexChanged: { if(currentIndex===3) nova.action('backups') } objectName: 'fileTabs'; Layout.fillWidth: true; background: Rectangle { color: 'transparent' }
                        NTab { text: 'Files' } NTab { text: 'Server settings' } NTab { text: 'Mods & plugins' } NTab { text: 'Backups' }
                    }
                    StackLayout { currentIndex: fileTabs.currentIndex; Layout.fillWidth: true; Layout.fillHeight: true
                        ColumnLayout {
                            RowLayout { Layout.fillWidth: true
                                BusyAction { text: '↑ Up'; implicitWidth: 70; enabled: !!s.browserPath && !s.busy; onClicked: nova.browseFiles(s.browserPath.split('/').slice(0,-1).join('/')) }
                                BusyAction { text: '⌂ Server'; implicitWidth: 94; onClicked: nova.browseFiles('') }
                                Field { text: 'Server / '+(s.browserPath || ''); readOnly: true; Layout.fillWidth: true }
                                BusyAction { text: 'Refresh'; onClicked: nova.browseFiles(s.browserPath || '') }
                            }
                            RowLayout { Layout.fillWidth: true; Layout.fillHeight: true; spacing: 12
                                Panel { Layout.preferredWidth: 310; Layout.minimumWidth: 260; Layout.fillHeight: true
                                    ColumnLayout { anchors.fill: parent; anchors.margins: 14; spacing: 10
                                        Field { id: fileFilter; placeholderText: 'Search this folder…'; Layout.fillWidth: true }
                                        RowLayout { Layout.fillWidth: true
                                            Caption { text: 'NAME'; Layout.fillWidth: true; font.pixelSize: 10 }
                                            Caption { text: 'SIZE'; font.pixelSize: 10 }
                                        }
                                        ListView { id: browserList; objectName: 'serverFileList'; Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 3; currentIndex: -1
                                            model: win.fileRows.filter(row=>row.name.toLowerCase().includes(fileFilter.text.toLowerCase()))
                                            delegate: ItemDelegate { required property var modelData; required property int index; objectName: 'browserItem_'+modelData.path; width: ListView.view.width; height: 40; hoverEnabled: true
                                                onHoveredChanged: if(hovered && enabled) uiAudio.play('hover')
                                                onClicked: { uiAudio.play('click'); browserList.currentIndex=index; if(modelData.folder) nova.browseFiles(modelData.path); else if(modelData.editable) nova.open_file(modelData.path) }
                                                background: Rectangle { radius: 10; color: browserList.currentIndex===index ? '#303b4c' : parent.hovered ? '#232b36' : 'transparent' }
                                                contentItem: RowLayout { spacing: 8
                                                    Item { Layout.preferredWidth: 21; Layout.preferredHeight: 18
                                                        Rectangle { visible: modelData.folder; x: 1; y: 1; width: 9; height: 5; radius: 2; color: '#e7bd6c' }
                                                        Rectangle { x: 1; y: modelData.folder ? 4 : 1; width: modelData.folder ? 19 : 14; height: modelData.folder ? 13 : 17; radius: 2; color: modelData.folder ? '#e7bd6c' : '#b7c5da'; border.color: modelData.folder ? '#f8d995' : '#d4ddeb' }
                                                    }
                                                    Text { text: modelData.name+(modelData.folder ? ' /' : ''); color: modelData.folder ? '#f0d49e' : '#e0e7f0'; Layout.fillWidth: true; elide: Text.ElideMiddle; font.pixelSize: 12 }
                                                    Text { text: modelData.folder ? 'FOLDER' : modelData.size<1024 ? modelData.size+' B' : Math.round(modelData.size/1024)+' KB'; color: '#8997aa'; font.pixelSize: 10 }
                                                }
                                            }
                                            ScrollBar.vertical: ScrollBar {}
                                        }
                                        Body { text: 'Click a folder to browse or a text file to edit. Binary files are listed with their size.'; Layout.fillWidth: true; font.pixelSize: 11 }
                                    }
                                }
                                ColumnLayout { Layout.fillWidth: true; Layout.fillHeight: true
                                    RowLayout { Layout.fillWidth: true
                                        Body { text: (s.file || 'Select a text file')+(s.dirty ? '  • Unsaved' : ''); Layout.fillWidth: true; maximumLineCount: 1; elide: Text.ElideLeft }
                                        BusyAction { text: 'Save file'; enabled: !!s.file && s.server==='Stopped' && !s.busy; primary: true; onClicked: nova.action('write') }
                                    }
                                    ScrollView { Layout.fillWidth: true; Layout.fillHeight: true; clip: true
                                        TextArea { id: editor; property bool syncing: false
                                            function syncText() { if(text!==s.editor) { syncing=true; text=s.editor; syncing=false } }
                                            Component.onCompleted: syncText()
                                            Connections { target: nova; function onChanged() { editor.syncText() } }
                                            color: '#d5dfef'; font.family: 'Consolas'; font.pixelSize: 13; selectByMouse: true; wrapMode: TextEdit.NoWrap
                                            background: Rectangle { color: '#10141c'; radius: 16; border.color: '#303741' }
                                            onTextChanged: if(!syncing && text!==s.editor) nova.update('editor',text)
                                        }
                                    }
                                }
                            }
                        }
                        ScrollView { id: propScroll; contentWidth: availableWidth; clip: true
                            ColumnLayout { width: propScroll.availableWidth; spacing: 12
                                Repeater { model: ['motd','server-name','gamemode','difficulty','max-players','view-distance','simulation-distance','level-name','level-seed','white-list','allow-list','pvp','allow-flight']
                                    RowLayout { required property string modelData; Layout.fillWidth: true
                                        Body { text: modelData; Layout.preferredWidth: 170 }
                                        Field { objectName: 'property_'+modelData; text: s.properties[modelData] || ''; Layout.fillWidth: true; enabled: s.filesLoaded && !s.exiting; onTextEdited: nova.property_value(modelData,text) }
                                    }
                                }
                                Body { text: (s.propertyDirty ? 'Unsaved changes. ' : '')+'Network settings use this profile’s ports; configure them in Settings.'; Layout.fillWidth: true }
                                BusyAction { text: 'Save server settings'; enabled: s.filesLoaded && s.server==='Stopped' && !s.busy; primary: true; onClicked: nova.action('properties') }
                            }
                        }
                        ColumnLayout {
                            RowLayout { Layout.fillWidth: true
                                Combo { id: addonKind; choices: ['mods','plugins'] }
                                Field { id: addonPath; placeholderText: 'Path to a mod or plugin JAR'; Layout.fillWidth: true }
                                BusyAction { text: 'Add JAR'; onClicked: nova.addon('add',addonKind.currentText,addonPath.text) }
                            }
                            ListView { Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 8; model: s.addons
                                delegate: RowLayout { required property var modelData; width: ListView.view.width
                                    Body { text: modelData.kind+' / '+modelData.name; Layout.fillWidth: true }
                                    BusyAction { text: modelData.name.endsWith('.disabled') ? 'Enable' : 'Disable'; onClicked: nova.addon('toggle',modelData.kind,modelData.name) }
                                    BusyAction { text: 'Remove'; danger: true; onClicked: nova.addon('remove',modelData.kind,modelData.name) }
                                }
                            }
                        }
                        ColumnLayout {
                            RowLayout {
                                BusyAction { text: 'Back up now'; primary: true; onClicked: nova.action('backup') }
                                BusyAction { text: 'Refresh backups'; onClicked: nova.action('backups') }
                            }
                            Body { text: 'Manual backups for this server. Stop hosting before backing up or restoring. Restore replaces current files after confirmation.'; Layout.fillWidth: true }
                            Body { visible: !(s.backups || []).length; text: 'No backups yet. Choose Back up now to save one.' }
                            ListView { Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 12; model: s.backups || []
                                delegate: RowLayout { required property var modelData; width: ListView.view.width
                                    ColumnLayout { Layout.fillWidth: true
                                        Body { text: modelData.name; Layout.fillWidth: true }
                                        Caption { text: new Date(modelData.modified*1000).toLocaleString() }
                                    }
                                    BusyAction { text: 'Restore'; enabled: s.server==='Stopped' && !s.busy; onClicked: nova.restoreBackup(modelData.path) }
                                }
                            }
                        }
                    }
                }
                }
                // SETTINGS
                ScrollView { id: settingsScroll; contentWidth: availableWidth; clip: true
                    ColumnLayout { width: settingsScroll.availableWidth-52; x: 26; spacing: 16
                        Heading { text: 'Make yourself at home.' }
                        SettingsSection { objectName: 'updateSettings'; title: 'Saturn updates'
                            ColumnLayout { id: updateColumn; Layout.fillWidth: true; spacing: 12
                                Caption { text: 'SATURN UPDATES · '+s.appVersion }
                                Body { text: s.updateStatus || ''; Layout.fillWidth: true }
                                RowLayout {
                                    Action { objectName: 'checkUpdatesButton'; text: 'Check for updates'; enabled: !s.updatePrivate && !s.updateBusy && !s.exiting; onClicked: nova.action('check_updates') }
                                    Action { text: 'Download update'; visible: !!s.updateAvailable && !s.updateReady; enabled: !s.updateBusy && !s.exiting; onClicked: nova.action('download_update') }
                                    Action { text: 'Install update'; visible: !!s.updateReady; primary: true; enabled: !s.updateBusy && !s.exiting; onClicked: nova.action('install_update') }
                                }
                                Body { text: s.updatePrivate ? 'This private build is delivered directly. Public updates are disabled.' : 'Checks include public beta releases. Downloads are verified against the release SHA-256 checksum. Stop all servers and tunnels before installing. Updates never install automatically.'; Layout.fillWidth: true }
                                Body { visible: !!s.updateAvailable; text: s.updateNotes || ''; textFormat: Text.PlainText; Layout.fillWidth: true; maximumLineCount: 12; elide: Text.ElideRight }
                            }
                        }

                        Body { text: 'Connection preferences save automatically. Passwords and passphrases stay in memory. CurseForge keys save encrypted for your Windows account.'; Layout.fillWidth: true }
                        SettingsSection { objectName: 'environmentSettings'; title: 'Environment'
                            Body { text: 'Java runtime for this server profile'; Layout.fillWidth: true }
                            Combo { objectName: 'javaVersionSelector'; choices: ['Auto','8','11','17','21','25']; currentIndex: choices.indexOf(s.java_version || 'Auto'); enabled: s.server==='Stopped' && !s.busy && !s.exiting; onActivated: nova.update('java_version',currentText); Layout.preferredWidth: 240 }
                            BusyAction { objectName: 'prepareJavaButton'; text: 'Download / prepare Java'; enabled: s.java_version!=='Auto' && s.engine!=='Bedrock' && s.server==='Stopped' && !s.busy; onClicked: nova.action('prepare_java') }
                            Body { text: 'Auto uses the Java runtime selected during installation. A selected version applies on the next start; prepare it first. Choose a version compatible with your Minecraft version and mod loader. Bedrock does not use Java. Downloads run in the background.'; Layout.fillWidth: true }
                        }
                        SettingsSection { objectName: 'storageSettings'; title: 'Main servers folder'
                            ColumnLayout { id: storageColumn; Layout.fillWidth: true; spacing: 12
                                Caption { text: 'MAIN SERVERS FOLDER' }
                                RowLayout { Layout.fillWidth: true
                                    Field { objectName: 'serversRootField'; text: nova.serversRoot; Layout.fillWidth: true; onEditingFinished: nova.setServersRoot(text) }
                                    BusyAction { text: 'Choose folder'; onClicked: nova.chooseServersRoot() }
                                }
                                Body { text: 'Choose this once. + Add automatically creates a named subfolder for each new server. Duplicate names get a number. Install / switch fills that folder with the server files. Existing worlds keep their current locations.'; Layout.fillWidth: true }
                            }
                        }
                        SettingsSection { objectName: 'hostingSettings'; title: 'Hosting connection'
                            ColumnLayout { Layout.fillWidth: true; spacing: 12
                                CheckBox { objectName: 'settingsUseVpsToggle'; text: 'Use VPS tunnel'; checked: s.use_vps!==false; enabled: s.server==='Stopped' && s.tunnel==='Disconnected' && !s.busy; palette.windowText: '#c0c8d8'; onToggled: nova.update('use_vps',checked) }
                                Body { text: s.use_vps===false ? 'Off: direct LAN / router port forwarding. No VPS, SSH credentials or tunnel is needed. Your router’s public IP is visible to players. Java binds to network interfaces when the server starts.' : 'On: Saturn forwards players through your VPS. Your saved SSH and VPS settings are used.'; Layout.fillWidth: true }
                                Body { visible: s.use_vps===false; text: '1. Find this PC’s LAN IPv4 with ipconfig and reserve it in your router.\n2. Forward the external port to that LAN IP and the profile’s local game port: Java TCP, Bedrock UDP.\n3. Allow the selected game port/program in Windows Firewall.\n4. Enter your public IP or domain in Domain & display. Start hosting, then test from outside your home network.\nRouter rules and firewall changes are manual. With CGNAT, double NAT or no router access, use a VPS tunnel or obtain a public IP from your ISP. Public joins from the same LAN may need router NAT loopback; test LAN joins using the PC’s LAN IP.'; Layout.fillWidth: true }
                                Action { visible: s.use_vps===false; text: 'Copy LAN address command'; onClicked: nova.copyHelpCommand('ipconfig') }
                                Body { visible: s.use_vps===false; text: 'Router forwarding: Java public TCP '+s.direct_java_port+' → PC LAN IP : '+s.local_java_port+'; Bedrock public UDP '+s.direct_bedrock_port+' → PC LAN IP : '+s.local_bedrock_port+'. Local ports are in Ports & ranges; public router ports are in Domain & display.'; Layout.fillWidth: true }
                            }
                        }
                        SettingsSection { objectName: 'connectionSettings'; title: 'VPS connection'; visible: s.use_vps!==false
                            ColumnLayout { id: connectionColumn; Layout.fillWidth: true; spacing: 12
                                Caption { text: 'VPS CONNECTION' }
                                Repeater { model: [{key:'vps_host',label:'VPS host / IP'},{key:'ssh_username',label:'SSH username'},{key:'ssh_port',label:'SSH port'},{key:'join_address',label:'Public join address'},{key:'key',label:'Local private key path (optional)'}]
                                    RowLayout { required property var modelData; Layout.fillWidth: true
                                        Body { text: modelData.label; Layout.preferredWidth: 190 }
                                        Field { text: String(s[modelData.key]); Layout.fillWidth: true; onTextEdited: nova.draft(modelData.key,text); onEditingFinished: nova.update(modelData.key,text); objectName: modelData.key+'Field' }
                                    }
                                }
                                RowLayout { Layout.fillWidth: true
                                    Body { text: 'SSH password'; Layout.preferredWidth: 190 }
                                    Field { text: nova.sshPassword; echoMode: TextInput.Password; Layout.fillWidth: true; onTextEdited: nova.update('password',text) }
                                }
                                RowLayout { Layout.fillWidth: true
                                    Body { text: 'Key passphrase'; Layout.preferredWidth: 190 }
                                    Field { text: nova.sshPassphrase; echoMode: TextInput.Password; Layout.fillWidth: true; onTextEdited: nova.update('passphrase',text) }
                                }
                                RowLayout {
                                    BusyAction { text: 'Configure VPS'; primary: true; onClicked: nova.action('configure') }
                                    BusyAction { text: 'Test connection'; onClicked: nova.action('test') }
                                    Action { text: 'Save preferences'; onClicked: nova.action('save') }
                                }
                            }
                        }
                        SettingsSection { objectName: 'portSettings'; title: 'Ports & ranges'
                            ColumnLayout { id: portColumn; Layout.fillWidth: true; spacing: 12
                                Caption { visible: s.use_vps!==false; text: 'VPS PORT RANGES' }
                                Body { visible: s.use_vps!==false; text: 'Allow extra public ports in advance. Use inclusive ranges or commas, e.g. 25565-25575, 25580. Leave blank to allow only assigned profile ports. Up to 256 additional ports per protocol.'; Layout.fillWidth: true }
                                Repeater { model: [{key:'java_port_ranges',label:'Java TCP range',example:'25565-25575'},{key:'bedrock_port_ranges',label:'Bedrock UDP range',example:'19132-19142'}]
                                    RowLayout { required property var modelData; visible: s.use_vps!==false; Layout.fillWidth: true
                                        Body { text: modelData.label; Layout.preferredWidth: 190 }
                                        Field { objectName: modelData.key+'Field'; text: s[modelData.key] || ''; placeholderText: modelData.example; Layout.fillWidth: true; enabled: !s.busy; onTextEdited: nova.draft(modelData.key,text); onEditingFinished: nova.update(modelData.key,text) }
                                    }
                                }
                                Body { visible: s.use_vps!==false; text: 'Save preferences, then Configure VPS to apply SSH and active UFW permissions. Existing profile ports stay included. New profiles inherit these ranges and take a free public port. Each server still listens on one port. Provider firewalls must allow the same ranges.'; Layout.fillWidth: true }
                                Caption { text: 'PROFILE GAME PORTS' }
                                Body { text: 'Each simultaneous server needs its own folder and local ports. Profiles on the same VPS also need unique public ports. Run Configure VPS after adding profiles or changing public ports.'; Layout.fillWidth: true }
                                Repeater { model: [{key:'local_java_port',label:'Java local TCP'},{key:'remote_java_port',label:'Java public TCP'},{key:'local_bedrock_port',label:'Bedrock local UDP'},{key:'bedrock_ipv6_port',label:'Bedrock local IPv6 UDP'},{key:'remote_bedrock_port',label:'Bedrock public UDP'}]
                                    RowLayout { required property var modelData; visible: s.use_vps!==false || !modelData.key.startsWith('remote_'); Layout.fillWidth: true
                                        Body { text: modelData.label; Layout.preferredWidth: 190 }
                                        Field { objectName: modelData.key+'Field'; text: String(s[modelData.key]); enabled: s.server==='Stopped' && !s.busy; Layout.fillWidth: true; onTextEdited: nova.draft(modelData.key,text); onEditingFinished: nova.update(modelData.key,text) }
                                    }
                                }
                            }
                        }
                        SettingsSection { objectName: 'dnsSettings'; title: 'Domain & display'
                            ColumnLayout { id: dnsColumn; Layout.fillWidth: true; spacing: 12
                                Caption { text: 'DOMAIN & DISPLAY' }
                                JoinAddressEditor { snapshot: win.s; Layout.fillWidth: true }
                                Body { text: 'At your domain panel, create an A record for '+((s.use_vps===false ? s.direct_join_address : s.join_address) || 'your game domain')+' pointing to '+(s.use_vps===false ? 'your router’s public IPv4 address' : (s.vps_host || 'your VPS IPv4 address'))+'. Use @ for the root domain. TTL of 1 hour is fine. If using Cloudflare, select DNS only. Changes here do not update DNS.'; Layout.fillWidth: true }
                                Body { visible: s.use_vps!==false; text: 'Java TCP: '+s.remote_java_port+'   •   Bedrock UDP: '+s.remote_bedrock_port+'\nVPS setup needs root or passwordless sudo. Allow every profile’s public port in provider firewalls.'; Layout.fillWidth: true }
                                Repeater { model: [{key:'direct_java_port',label:'Router public Java TCP'},{key:'direct_bedrock_port',label:'Router public Bedrock UDP'}]
                                    RowLayout { required property var modelData; visible: s.use_vps===false; Layout.fillWidth: true
                                        Body { text: modelData.label; Layout.preferredWidth: 190 }
                                        Field { objectName: modelData.key+'Field'; text: String(s[modelData.key]); enabled: s.server==='Stopped' && !s.busy; Layout.fillWidth: true; onTextEdited: nova.draft(modelData.key,text); onEditingFinished: nova.update(modelData.key,text) }
                                    }
                                }
                                SoundSwitch { text: 'Play startup scene'; checked: s.startup_animation!==false; palette.windowText: '#c0c8d8'; onToggled: nova.update('startup_animation',checked) }
                                SoundSwitch { objectName: 'soundEnabledToggle'; text: 'Enable sounds'; checked: s.sound_enabled!==false; palette.windowText: '#c0c8d8'; onToggled: { nova.update('sound_enabled',checked); if(checked) uiAudio.play('click') } }
                                Body { text: 'Mute all startup, hover, click and transition sounds with this switch.'; Layout.fillWidth: true }
                                SoundSwitch { objectName: 'startupSoundToggle'; text: 'Startup sound'; checked: s.startup_sound!==false; palette.windowText: '#c0c8d8'; onToggled: nova.update('startup_sound',checked) }
                                RowLayout {
                                    Body { text: 'Sound volume'; Layout.preferredWidth: 125 }
                                    Slider { objectName: 'startupVolume'; onPressedChanged: if(pressed) uiAudio.play('click'); from: 0; to: 1; value: s.sound_volume===undefined ? 0.3 : s.sound_volume; stepSize: 0.05; Layout.preferredWidth: 240; onMoved: nova.update('sound_volume',value) }
                                    Body { text: Math.round((s.sound_volume===undefined ? 0.3 : s.sound_volume)*100)+'%' }
                                }
                                Action { text: 'Preview startup scene'; enabled: !s.reduced; onClicked: intro.begin() }
                                SoundSwitch { text: 'Reduce motion'; checked: s.reduced; palette.windowText: '#c0c8d8'; onToggled: nova.update('reduced',checked) }
                                Body { text: 'Closing the window keeps hosting in the tray. Right-click Saturn’s tray icon and choose Exit Saturn to save the world and stop its processes.'; Layout.fillWidth: true }
                            }
                        }
                        Item { implicitHeight: 20 }
                    }
                }
                // PLAYERS
                Item { ColumnLayout {
                    anchors.fill: parent; anchors.margins: 26; spacing: 16
                    Heading { text: 'Your players, in one place.' }
                    Body { text: 'Online players refresh every 15 seconds from this profile’s console. Modded/custom server output may require manual refresh. Commands apply only to the selected profile.'; Layout.fillWidth: true }
                    RowLayout {
                        Action { text: 'Refresh players'; onClicked: nova.playerAction('refresh','') }
                        Action { text: 'Allowlist on'; onClicked: nova.playerAction('whitelist_on','') }
                        Action { text: 'Allowlist off'; onClicked: nova.playerAction('whitelist_off','') }
                    }
                    Panel { Layout.fillWidth: true; Layout.fillHeight: true
                        ColumnLayout { anchors.fill: parent; anchors.margins: 20; spacing: 12
                            Caption { text: 'ONLINE · '+(s.players || []).length }
                            Body { visible: !(s.players || []).length; text: s.server==='Stopped' ? 'Start this server to see its player list.' : 'No online players reported yet.' }
                            ListView { Layout.fillWidth: true; Layout.fillHeight: true; clip: true; model: s.players || []; spacing: 8
                                delegate: Action { required property string modelData; width: ListView.view.width; text: '♙  '+modelData; onClicked: playerTarget.text=modelData }
                            }
                            Field { id: playerTarget; placeholderText: 'Click a player or enter a player name'; Layout.fillWidth: true }
                            Flow { Layout.fillWidth: true; spacing: 8
                                Repeater { model: [{label:'Kick',action:'kick'},{label:'Ban (Java)',action:'ban'},{label:'Pardon (Java)',action:'pardon'},{label:'Make operator',action:'op'},{label:'Remove operator',action:'deop'},{label:'Add to allowlist',action:'allow'},{label:'Remove from allowlist',action:'unallow'}]
                                    Action { required property var modelData; text: modelData.label; onClicked: nova.playerAction(modelData.action,playerTarget.text) }
                                }
                            }
                            Body { text: 'Operator and moderation actions ask for confirmation. Bedrock supports kick, op/deop and allowlist; native ban/pardon is Java only.'; Layout.fillWidth: true }
                        }
                    }
                } }
                Item { ColumnLayout { anchors.fill: parent; anchors.margins: 26; spacing: 12
                    Heading { text: 'Your hosting tasks.' }
                    Body { text: 'Run now or set a saved schedule. '+s.scheduleTimezone+'. Saturn must be open; runs missed while closed or paused are skipped.'; Layout.fillWidth: true }
                    RowLayout { Layout.fillWidth: true
                        Action { objectName: 'newTaskButton'; text: '+ New task'; primary: true; onClicked: taskCreator.open() }
                        Body { text: 'Choose a task, how often it runs and a 12-hour time. No date entry needed.'; Layout.fillWidth: true }
                    }
                    RowLayout { Layout.fillWidth: true
                        TabBar { id: taskViews; Layout.fillWidth: true; background: Item {}
                            NTab { text: 'Saved schedules' } NTab { text: 'Queue & history' }
                        }
                        Action { text: s.queuePaused ? 'Resume tasks' : 'Pause tasks'; onClicked: nova.action(s.queuePaused ? 'queue_run' : 'queue_pause') }
                    }
                    StackLayout { currentIndex: taskViews.currentIndex; Layout.fillWidth: true; Layout.fillHeight: true
                        Item { ColumnLayout { anchors.fill: parent
                            Body { visible: !(s.schedules || []).length; text: 'No schedules yet. Choose New task to set an action, frequency and time.'; Layout.fillWidth: true }
                            ListView { objectName: 'hostScheduleList'; Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 10; model: s.schedules || []
                                delegate: Panel { required property var modelData; width: ListView.view.width; height: scheduleRow.implicitHeight+28
                                    RowLayout { id: scheduleRow; anchors.fill: parent; anchors.margins: 14; spacing: 10
                                        SoundSwitch { checked: !!modelData.enabled; onToggled: nova.enableSchedule(modelData.id,checked) }
                                        ColumnLayout { Layout.fillWidth: true; spacing: 5
                                            Text { text: modelData.label+' · '+modelData.server; color: '#edf1f7'; font.pixelSize: 14 }
                                            Body { text: (modelData.next_due ? Qt.formatDateTime(new Date(modelData.next_due*1000),'ddd, MMM d · h:mm AP') : 'No future run')+' · '+({'once':'One time','daily':'Daily','weekdays':'Weekdays','weekly':'Weekly','biweekly':'Every 2 weeks','monthly':'Monthly'}[modelData.repeat])+' · '+modelData.last_status; Layout.fillWidth: true; textFormat: Text.PlainText }
                                            Body { visible: modelData.operation==='command'; text: modelData.command || ''; Layout.fillWidth: true; textFormat: Text.PlainText }
                                        }
                                        Action { text: 'Remove'; onClicked: nova.removeSchedule(modelData.id) }
                                    }
                                }
                                ScrollBar.vertical: ScrollBar {}
                            }
                        } }
                        ColumnLayout {
                            RowLayout { Action { text: 'Run queue'; onClicked: nova.action('queue_run') } Action { text: 'Clear finished'; onClicked: nova.action('queue_clear') } }
                            ListView { objectName: 'hostTaskList'; Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 10; model: s.tasks || []
                                delegate: Panel { required property var modelData; width: ListView.view.width; height: taskRow.implicitHeight+28
                                    RowLayout { id: taskRow; anchors.fill: parent; anchors.margins: 14; spacing: 10
                                        ColumnLayout { Layout.fillWidth: true; spacing: 5
                                            Text { text: modelData.label+' · '+modelData.server; color: '#edf1f7'; font.pixelSize: 14 }
                                            Body { text: modelData.status+(modelData.detail ? ' · '+modelData.detail : ''); Layout.fillWidth: true; textFormat: Text.PlainText }
                                            Body { visible: modelData.operation==='command'; text: modelData.command || ''; Layout.fillWidth: true; textFormat: Text.PlainText }
                                        }
                                        Action { text: 'Remove'; visible: modelData.status!=='Running'; onClicked: nova.removeTask(modelData.id) }
                                    }
                                }
                                ScrollBar.vertical: ScrollBar {}
                            }
                        }
                    }
                } }
                HelpPage { snapshot: win.s }
            }
            Rectangle { Layout.fillWidth: true; implicitHeight: 38; color: '#10141d'
                RowLayout { anchors.fill: parent; anchors.leftMargin: 26; anchors.rightMargin: 26
                    BusyIndicator { running: s.busy || s.exiting; visible: running; implicitWidth: 22; implicitHeight: 22 }
                    Text { text: s.activity; color: '#9faec5'; font.pixelSize: 11; Layout.fillWidth: true }
                    Text { text: (s.hostingCount || 0)+' hosting  ·  '+(s.joinDisplay || s.join_address); color: '#9faec5'; font.pixelSize: 11 }
                }
            }
        }
    }
    Component {
        id: packBrowserComponent
Item { ColumnLayout {
                    anchors.fill: parent; anchors.leftMargin: 26; anchors.rightMargin: 26; anchors.bottomMargin: 18; spacing: 12
                    RowLayout { Layout.fillWidth: true
                        ColumnLayout { Layout.fillWidth: true; spacing: 6
                            Heading { text: 'Find your next world.'; font.pixelSize: 28 }
                            Body { text: 'Discover CurseForge packs, explore their mods and choose a server-ready release.'; Layout.fillWidth: true; font.pixelSize: 12 }
                        }
                        Action { text: 'API key'; implicitHeight: 36; onClicked: win.showPackApi=!win.showPackApi }
                    }
                    Panel { visible: win.showPackApi || !nova.apiKey.length; Layout.fillWidth: true; implicitHeight: apiRow.implicitHeight+24
                        RowLayout { id: apiRow; anchors.fill: parent; anchors.margins: 12
                            Field { id: api; placeholderText: 'Your CurseForge API key · encrypted on this PC'; text: nova.apiKey; echoMode: TextInput.Password; Layout.fillWidth: true; onTextEdited: nova.update('apiKey',text); onEditingFinished: nova.saveApiKey() }
                            Action { text: 'Forget'; onClicked: nova.forgetApiKey() }
                            Action { text: 'Get a key'; onClicked: Qt.openUrlExternally('https://support.curseforge.com/support/solutions/articles/9000208346-about-the-curseforge-api-and-how-to-apply-for-a-key') }
                        }
                    }
                    RowLayout { Layout.fillWidth: true; spacing: 10
                        Field { id: search; objectName: 'packSearch'; placeholderText: 'Search by pack name or adventure…'; Layout.fillWidth: true; onAccepted: nova.query(text,sort.currentText,mc.text,0) }
                        Combo { id: sort; choices: ['Popular','Relevant','Recently updated','Most downloaded']; Layout.preferredWidth: 180; onActivated: nova.query(search.text,currentText,mc.text,0) }
                        Field { id: mc; placeholderText: 'MC version'; Layout.preferredWidth: 110 }
                        BusyAction { text: 'Search'; primary: true; implicitWidth: 90; onClicked: nova.query(search.text,sort.currentText,mc.text,0) }
                    }
                    Body { visible: !!s.error; text: s.error || ''; color: '#ffb3c2'; Layout.fillWidth: true }
                    RowLayout { Layout.fillWidth: true; Layout.fillHeight: true; spacing: 14
                        Item { Layout.fillWidth: true; Layout.fillHeight: true
                            GridView { id: gallery; objectName: 'packGallery'; anchors.fill: parent; visible: s.packs.length>0; clip: true; cellWidth: Math.floor(width/Math.max(1,Math.floor(width/270))); cellHeight: 210; model: s.packs; cacheBuffer: 210; reuseItems: true
                                delegate: Item { required property var modelData; required property int index; width: gallery.cellWidth; height: gallery.cellHeight
                                    Panel { anchors.fill: parent; anchors.rightMargin: 10; anchors.bottomMargin: 10
                                        border.color: modelData.id===s.project.id ? '#97a6bc' : packHover.hovered ? '#617086' : '#303741'
                                        ColumnLayout { anchors.fill: parent; anchors.margins: 16; spacing: 10
                                            RowLayout { Layout.fillWidth: true; spacing: 12
                                                Rectangle { Layout.preferredWidth: 64; Layout.preferredHeight: 64; radius: 16; color: '#0c1118'; border.color: '#303b4a'
                                                    SaturnMark { anchors.fill: parent; opacity: 0.55; visible: packArt.status!==Image.Ready }
                                                    Image { id: packArt; anchors.fill: parent; anchors.margins: 5; source: (modelData.logo || {}).thumbnailUrl || ''; asynchronous: true; cache: true; sourceSize.width: 128; sourceSize.height: 128; fillMode: Image.PreserveAspectFit }
                                                }
                                                ColumnLayout { Layout.fillWidth: true; spacing: 5
                                                    Text { text: modelData.name; color: '#edf1f9'; font.pixelSize: 15; font.weight: Font.DemiBold; maximumLineCount: 2; wrapMode: Text.WordWrap; elide: Text.ElideRight; Layout.fillWidth: true }
                                                    Text { text: modelData.authors && modelData.authors.length ? 'by '+modelData.authors[0].name : 'CurseForge'; color: '#8c9ab0'; font.pixelSize: 10; elide: Text.ElideRight; Layout.fillWidth: true }
                                                }
                                            }
                                            Body { text: modelData.summary || 'Explore the release details and included mods.'; maximumLineCount: 2; elide: Text.ElideRight; Layout.fillWidth: true; font.pixelSize: 11 }
                                            Item { Layout.fillHeight: true }
                                            RowLayout { Layout.fillWidth: true
                                                Caption { text: Number(modelData.downloadCount || 0).toLocaleString()+' downloads'; font.pixelSize: 9; font.letterSpacing: 0; Layout.fillWidth: true }
                                                BusyAction { text: 'View details'; implicitWidth: 100; implicitHeight: 32; onClicked: nova.project(index,0) }
                                            }
                                        }
                                        HoverHandler { id: packHover; onHoveredChanged: if(hovered) uiAudio.play('hover') }
                                    }
                                }
                                ScrollBar.vertical: ScrollBar {}
                            }
                            Panel { anchors.fill: parent; visible: !s.packs.length
                                ColumnLayout { anchors.centerIn: parent; width: parent.width-56; spacing: 14
                                    SaturnMark { Layout.alignment: Qt.AlignHCenter; Layout.preferredWidth: 145; Layout.preferredHeight: 110 }
                                    Text { text: s.busy ? 'Finding your next adventure…' : nova.apiKey.length ? 'Your next adventure is out there.' : 'Connect to CurseForge'; color: '#e6edf8'; font.pixelSize: 21; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter; Layout.fillWidth: true }
                                    Body { text: s.busy ? s.activity : nova.apiKey.length ? 'Choose a sort and search to explore packs. Try a different name or Minecraft version if there are no results.' : 'Add your own API key above, then browse popular packs and server-ready releases.'; horizontalAlignment: Text.AlignHCenter; Layout.fillWidth: true }
                                    BusyAction { text: 'Browse popular packs'; Layout.alignment: Qt.AlignHCenter; enabled: !!nova.apiKey.length && !s.busy; onClicked: nova.query('','Popular','',0) }
                                }
                            }
                        }
                        Panel { Layout.preferredWidth: 310; Layout.fillHeight: true
                            ScrollView { id: detail; anchors.fill: parent; anchors.margins: 18; contentWidth: availableWidth; clip: true
                                ColumnLayout { width: detail.availableWidth; spacing: 12
                                    Rectangle { Layout.alignment: Qt.AlignHCenter; width: 88; height: 88; radius: 20; color: '#0b1017'; border.color: '#303b4a'
                                        SaturnMark { anchors.fill: parent; visible: detailArt.status!==Image.Ready; opacity: 0.7 }
                                        Image { id: detailArt; anchors.fill: parent; anchors.margins: 8; source: (s.project.logo || {}).thumbnailUrl || ''; asynchronous: true; sourceSize.width: 160; sourceSize.height: 160; fillMode: Image.PreserveAspectFit }
                                    }
                                    Caption { text: s.project.id ? 'PACK DETAILS' : 'YOUR NEXT SERVER'; font.pixelSize: 9; Layout.alignment: Qt.AlignHCenter }
                                    Text { text: s.project.name || 'Select a modpack'; color: '#f1f3fa'; font.pixelSize: 22; wrapMode: Text.WordWrap; Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter }
                                    Body { text: s.project.summary || 'Select View details on a pack to compare releases and explore its mods.'; Layout.fillWidth: true }
                                    SoundSwitch { visible: !!s.project.id; text: 'Server-ready releases only'; checked: win.serverReleasesOnly; palette.windowText: '#c8d3e5'; onToggled: win.serverReleasesOnly=checked }
                                    Combo { objectName: 'packReleaseSelector'; visible: !!s.project.id; choices: win.packReleases().map(item=>item.row.displayName || item.row.fileName); currentIndex: win.packReleases().findIndex(item=>item.index===s.releaseIndex); Layout.fillWidth: true; onActivated: { const rows=win.packReleases(); if(currentIndex>=0 && currentIndex<rows.length) nova.update('releaseIndex',rows[currentIndex].index) } }
                                    Body { visible: !!s.project.id && !win.packReleases().length; text: 'No matching server-ready release on this page. Try Older releases or turn the filter off.'; font.pixelSize: 11; Layout.fillWidth: true }
                                    BusyAction { objectName: 'selectPackForServer'; text: 'Select for this server'; primary: true; Layout.fillWidth: true; enabled: !!(s.releases[s.releaseIndex] || {}).serverPackFileId && !s.busy; onClicked: { nova.action('pick'); if(s.cf_pack.project_id===s.project.id && s.cf_pack.file_id===(s.releases[s.releaseIndex] || {}).id) { win.page=1; packBrowserPopup.close() } } }
                                    Body { visible: !!s.project.id; text: 'Selection opens Server controls. Install there after accepting the Minecraft EULA.'; font.pixelSize: 11; Layout.fillWidth: true }
                                    RowLayout {
                                        BusyAction { text: 'Older releases'; enabled: !!s.project.id && !s.busy; implicitWidth: 115; onClicked: nova.action('older') }
                                        Action { text: 'Website'; enabled: !!s.project.links; implicitWidth: 95; onClicked: Qt.openUrlExternally(s.project.links.websiteUrl) }
                                    }
                                    BusyAction { text: 'Explore mod list'; Layout.fillWidth: true; enabled: s.releases.length>0 && !s.busy; onClicked: nova.action('mods') }
                                    Field { id: modSearch; visible: s.mods.length>0; placeholderText: 'Filter included mods…'; Layout.fillWidth: true }
                                    Repeater { model: s.mods.filter(m=>m.name.toLowerCase().includes(modSearch.text.toLowerCase()))
                                        RowLayout { required property var modelData; Layout.fillWidth: true
                                            Image { source: modelData.logo || ''; asynchronous: true; sourceSize.width: 48; sourceSize.height: 48; Layout.preferredWidth: 28; Layout.preferredHeight: 28; fillMode: Image.PreserveAspectFit }
                                            Body { text: modelData.name; Layout.fillWidth: true; font.pixelSize: 11 }
                                        }
                                    }
                                    Body { visible: s.mods.length>0; text: 'This is the client manifest mod list; server contents can differ.'; font.pixelSize: 10; Layout.fillWidth: true }
                                }
                            }
                        }
                    }
                    RowLayout {
                        BusyAction { text: '← Previous'; implicitWidth: 112; enabled: s.pageIndex>=20 && !s.busy; onClicked: nova.query(search.text,sort.currentText,mc.text,s.pageIndex-20) }
                        Body { text: s.packs.length ? 'Page '+(Math.floor(s.pageIndex/20)+1)+' · '+s.packs.length+' packs' : 'CurseForge discovery'; Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter; font.pixelSize: 11 }
                        BusyAction { text: 'Next →'; implicitWidth: 100; enabled: s.packs.length===20 && !s.busy; onClicked: nova.query(search.text,sort.currentText,mc.text,s.pageIndex+20) }
                    }
                } }
    }
    Popup {
        id: packBrowserPopup; objectName: 'packBrowserPopup'; parent: Overlay.overlay
        onOpened: { uiAudio.play('transition'); if(nova.apiKey.length && !s.packs.length && !s.busy) nova.query('','Popular','',0) }
        onClosed: uiAudio.play('transition')
        modal: true; focus: true; closePolicy: Popup.CloseOnEscape
        width: Math.min(1180,win.width-48); height: Math.min(780,win.height-48)
        x: (win.width-width)/2; y: (win.height-height)/2; padding: 18
        background: Panel { radius: 26; border.color: '#65738a' }
        Overlay.modal: Rectangle { color: '#ad05070b' }
        contentItem: ColumnLayout { spacing: 16
            RowLayout { Layout.fillWidth: true
                Caption { text: 'BROWSE MODPACKS · '+s.profileName; Layout.fillWidth: true }
                Action { text: 'Close'; implicitHeight: 34; onClicked: packBrowserPopup.close() }
            }
            Loader { Layout.fillWidth: true; Layout.fillHeight: true; active: packBrowserPopup.visible; sourceComponent: packBrowserComponent }
        }
    }
    Popup {
        id: taskCreator; objectName: 'taskCreatePopup'; parent: Overlay.overlay
        modal: true; focus: true; closePolicy: Popup.CloseOnEscape
        width: Math.min(560,win.width-48); x: (win.width-width)/2; y: (win.height-height)/2
        padding: 24; implicitHeight: creatorColumn.implicitHeight+48
        background: Panel { radius: 26; border.color: '#65738a' }
        Overlay.modal: Rectangle { color: '#ad05070b' }
        onClosed: uiAudio.play('transition')
        onOpened: {
            uiAudio.play('transition')
            nova.beginTaskCreation()
            const next=new Date(Date.now()+3600000)
            taskHour.currentIndex=(next.getHours()%12 || 12)-1
            taskMinute.currentIndex=0
            taskPeriod.currentIndex=next.getHours()>=12 ? 1 : 0
        }
        contentItem: ColumnLayout { id: creatorColumn; spacing: 16
            Heading { text: 'Create a task'; font.pixelSize: 25 }
            Body { text: 'For '+s.profileName+' · '+s.scheduleTimezone; Layout.fillWidth: true }
            Caption { text: 'TASK'; font.pixelSize: 10 }
            Combo { id: creatorTask; objectName: 'hostTaskType'; choices: ['Start','Stop','Save world','Backup','Custom command']; Layout.fillWidth: true; enabled: !s.exiting }
            Field { id: creatorCommand; objectName: 'customTaskCommand'; visible: creatorTask.currentIndex===4; placeholderText: 'Minecraft console command'; maximumLength: 512; Layout.fillWidth: true }
            Caption { text: 'HOW OFTEN'; font.pixelSize: 10 }
            Combo { id: creatorRepeat; objectName: 'taskRepeat'; choices: ['One time','Daily','Weekdays','Weekly','Every 2 weeks','Monthly']; currentIndex: 1; Layout.fillWidth: true; enabled: !s.exiting }
            Caption { text: 'TIME'; font.pixelSize: 10 }
            RowLayout { Layout.fillWidth: true; spacing: 10
                Combo { id: taskHour; objectName: 'taskHour'; choices: Array.from({length:12},(_,i)=>String(i+1)); Layout.fillWidth: true; implicitWidth: 100; enabled: !s.exiting }
                Text { text: ':'; color: '#e6edf7'; font.pixelSize: 24 }
                Combo { id: taskMinute; objectName: 'taskMinute'; choices: Array.from({length:60},(_,i)=>String(i).padStart(2,'0')); Layout.fillWidth: true; implicitWidth: 100; enabled: !s.exiting }
                Combo { id: taskPeriod; objectName: 'taskPeriod'; choices: ['AM','PM']; Layout.preferredWidth: 140; enabled: !s.exiting }
            }
            Body { text: nova.previewTaskTime(taskHour.currentIndex+1,taskMinute.currentIndex,taskPeriod.currentText,['once','daily','weekdays','weekly','biweekly','monthly'][creatorRepeat.currentIndex]); Layout.fillWidth: true }
            Body { text: 'The first run is the next matching time. Repeats follow from that run. Backup briefly stops running servers, then restarts and reconnects them. Saturn must stay open.'; Layout.fillWidth: true; font.pixelSize: 11 }
            Body { visible: !!s.taskCreateError; text: s.taskCreateError || ''; color: '#ffb3c2'; Layout.fillWidth: true }
            RowLayout { Layout.alignment: Qt.AlignRight
                Action { text: 'Cancel'; onClicked: taskCreator.close() }
                Action { text: 'Run now'; onClicked: { if(nova.runTask(['start','stop','save_world','backup','command'][creatorTask.currentIndex],creatorCommand.text)) taskCreator.close() } }
                Action { objectName: 'saveTimedTask'; text: 'Save task'; primary: true; onClicked: {
                    if(nova.createTimedTask(['start','stop','save_world','backup','command'][creatorTask.currentIndex],taskHour.currentIndex+1,taskMinute.currentIndex,taskPeriod.currentText,['once','daily','weekdays','weekly','biweekly','monthly'][creatorRepeat.currentIndex],creatorCommand.text)) taskCreator.close()
                } }
            }
        }
    }
    StartupScene { id: intro; objectName: 'startupScene'; anchors.fill: parent; z: 90; reduced: !!s.reduced; playOnStart: s.startup_animation!==false; soundEnabled: s.sound_enabled!==false && s.startup_sound!==false; soundVolume: s.sound_volume===undefined ? 0.3 : s.sound_volume }
    // Confirmation is embedded in this window, including first SSH host trust.
    Rectangle { anchors.fill: parent; color: '#b0000000'; visible: !!s.dialog; z: 100
        MouseArea { anchors.fill: parent }
        Panel { width: 540; height: dialogColumn.implicitHeight+48; anchors.centerIn: parent
            ColumnLayout { id: dialogColumn; anchors.fill: parent; anchors.margins: 24; spacing: 18
                Text { text: s.dialogTitle; color: '#f2f4fc'; font.pixelSize: 24; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Body { text: s.dialog; Layout.fillWidth: true }
                RowLayout { Layout.alignment: Qt.AlignRight
                    Action { text: 'Cancel'; onClicked: nova.answer(false) }
                    Action { text: 'Continue'; primary: true; onClicked: nova.answer(true) }
                }
            }
        }
    }
    onPageChanged: {
        uiAudio.play('transition')
        if(!s.reduced) fade.restart()
        if(win.page===3) nova.action('ensure_files')
    }
    ParallelAnimation { id: fade
        NumberAnimation { target: pages; property: 'opacity'; from: 0.25; to: 1; duration: 240; easing.type: Easing.OutCubic }
        NumberAnimation { target: pages; property: 'revealOffset'; from: 18; to: 0; duration: 300; easing.type: Easing.OutCubic }
    }
    Connections { target: nova
        function onChanged() {
            win.syncServers(); win.syncFileRows()
            const selected=s.profileIndex || 0
            if(selected!==win.shownProfileIndex) {
                win.shownProfileIndex=selected
                if(!s.reduced) fade.restart()
            }
            if(s.reduced) { fade.stop(); pages.opacity=1; pages.revealOffset=0 }
        }
    }
}
