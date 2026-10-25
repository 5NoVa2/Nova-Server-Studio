import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: win
    visible: true; width: 1260; height: 850; minimumWidth: 1040; minimumHeight: 700
    title: 'Nova | Minecraft Server Studio'; color: '#090b10'
    property var s: nova.state
    property int page: 0
    property int shownProfileIndex: 0
    property bool full: false
    property var titles: ['Home','Server','Modpacks','Files','Settings','Players']
    property color muted: '#8e96a8'
    font.family: 'Segoe UI'
    onClosing: function(close) { close.accepted=false; nova.action('tray') }
    Component.onCompleted: shownProfileIndex=s.profileIndex || 0
    function fullscreen() { full=!full; if(full) showFullScreen(); else showNormal() }
    Shortcut { sequence: 'F11'; onActivated: win.fullscreen() }
    Shortcut { sequence: 'Escape'; onActivated: { if(win.full) win.fullscreen() } }
    Shortcut { sequence: 'Ctrl+S'; onActivated: nova.action('save_all') }
    component Caption: Text { color: win.muted; font.pixelSize: 12; font.letterSpacing: 1.3 }
    component Heading: Text { color: '#f0f1f7'; font.pixelSize: 29; font.weight: Font.DemiBold }
    component Body: Text { color: '#a4adbe'; font.pixelSize: 13; wrapMode: Text.WordWrap }
    component Action: NButton { motion: !s.reduced; enabled: !s.exiting }
    component Field: NField { enabled: !s.exiting }
    component Combo: NCombo { enabled: !s.busy && !s.exiting }
    component BusyAction: Action { enabled: !s.busy && !s.exiting }
    Rectangle { anchors.fill: parent; gradient: Gradient { GradientStop { position: 0; color: '#10141e' } GradientStop { position: 0.7; color: '#090b10' } } }
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
        anchors.fill: parent; spacing: 0
        Rectangle {
            Layout.preferredWidth: 188; Layout.fillHeight: true; color: '#10131a'; border.color: '#202631'
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 20; spacing: 10
                Text { text: 'N O V A'; color: '#f3f4fa'; font.pixelSize: 25; font.weight: Font.Bold; Layout.topMargin: 12 }
                Caption { text: 'SERVER STUDIO'; font.pixelSize: 9; Layout.bottomMargin: 38 }
                Repeater {
                    model: win.titles
                    Action {
                        required property string modelData; required property int index
                        text: ['◈  ','▷  ','▦  ','≡  ','⚙  ','♙  '][index]+modelData
                        Layout.fillWidth: true; primary: win.page===index
                        onClicked: win.page=index
                    }
                }
                Item { Layout.fillHeight: true }
                Caption { text: 'CREATED BY NOVA'; font.pixelSize: 9 }
                Action { text: 'Minimize to tray'; Layout.fillWidth: true; onClicked: nova.action('tray') }
                Action { text: 'Exit Nova'; danger: true; Layout.fillWidth: true; onClicked: nova.action('exit') }
            }
        }
        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; spacing: 0
            RowLayout {
                Layout.fillWidth: true; Layout.margins: 26; spacing: 14
                Caption { text: win.page===0 ? 'YOUR WORLD. YOUR RULES.' : win.titles[win.page].toUpperCase(); Layout.fillWidth: true }
                Rectangle { width: 7; height: 7; radius: 4; color: s.server==='Ready' ? '#9ee2bd' : s.server==='Starting' ? '#e8cc95' : '#666e7e' }
                Text { text: s.server; color: '#b9c1cf'; font.pixelSize: 12 }
                Text { text: '•  '+s.tunnel; color: win.muted; font.pixelSize: 12 }
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
            StackLayout {
                id: pages; property real revealOffset: 0; transform: Translate { y: pages.revealOffset } currentIndex: win.page; Layout.fillWidth: true; Layout.fillHeight: true
                // HOME
                Item {
                    ColumnLayout {
                        id: homeLayout; property bool compact: parent.height<620
                        anchors.centerIn: parent; width: Math.min(parent.width-64,850); spacing: compact ? 12 : 20
                        Caption { text: 'MINECRAFT, WITHOUT THE FRICTION'; Layout.alignment: Qt.AlignHCenter }
                        Text { text: 'Welcome to your\nnext world.'; color: '#f5f6fc'; font.pixelSize: homeLayout.compact ? 40 : 56; font.weight: Font.Light; horizontalAlignment: Text.AlignHCenter; Layout.alignment: Qt.AlignHCenter }
                        Body { text: 'Create, host and shape your server. All in one place.'; Layout.alignment: Qt.AlignHCenter; Layout.bottomMargin: homeLayout.compact ? 8 : 24 }
                        RowLayout {
                            spacing: 14; Layout.fillWidth: true
                            Repeater {
                                model: [{title:'Control center',sub:'Build your server',icon:'◇',page:1},{title:'Discover packs',sub:'Find your next adventure',icon:'▦',page:2},{title:'Your workspace',sub:'Files, mods & settings',icon:'≡',page:3}]
                                Panel {
                                    required property var modelData
                                    Layout.fillWidth: true; Layout.preferredHeight: homeLayout.compact ? 138 : 184
                                    scale: tile.hovered ? 1.025 : 1
                                    border.color: tile.hovered ? '#68758f' : '#303744'
                                    Behavior on scale { NumberAnimation { duration: s.reduced ? 0 : 160 } }
                                    Column { anchors.centerIn: parent; spacing: 12
                                        Text { text: modelData.icon; color: '#e3e8f6'; font.pixelSize: 46; anchors.horizontalCenter: parent.horizontalCenter }
                                        Text { text: modelData.title; color: '#f0f2f8'; font.pixelSize: 16; anchors.horizontalCenter: parent.horizontalCenter }
                                        Text { text: modelData.sub; color: win.muted; font.pixelSize: 11; anchors.horizontalCenter: parent.horizontalCenter }
                                    }
                                    HoverHandler { id: tile }
                                    TapHandler { onTapped: win.page=modelData.page }
                                }
                            }
                        }
                        RowLayout { Layout.alignment: Qt.AlignHCenter; Layout.topMargin: homeLayout.compact ? 0 : 16
                            BusyAction { text: '▷  Start hosting'; primary: true; implicitWidth: 190; onClicked: { win.page=1; nova.action('hosting') } }
                            Body { text: s.joinDisplay || s.join_address; Layout.leftMargin: 12 }
                        }
                    }
                }
                // SERVER
                ScrollView {
                    id: serverScroll; clip: true; contentWidth: availableWidth
                    ColumnLayout {
                        width: serverScroll.availableWidth-52; x: 26; spacing: 18
                        Heading { text: (s.profileName || 'Your server')+', at a glance.'; Layout.fillWidth: true; elide: Text.ElideRight }
                        RowLayout { Layout.fillWidth: true; spacing: 12
                            Repeater { model: [{label:'SERVER',value:s.server},{label:'TUNNEL',value:s.tunnel},{label:'UPTIME',value:s.uptime}]
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
                            BusyAction { text: 'Start local'; onClicked: nova.action('start') }
                            BusyAction { text: 'Connect tunnel'; onClicked: nova.action('tunnel') }
                            Action { text: 'Stop hosting'; danger: true; onClicked: nova.action('stop') }
                            Action { text: 'Copy address'; onClicked: nova.action('copy') }
                            Action { text: 'Players'; onClicked: win.page=5 }
                        }
                        Panel { Layout.fillWidth: true; implicitHeight: installColumn.implicitHeight+40
                            ColumnLayout { id: installColumn; anchors.fill: parent; anchors.margins: 20; spacing: 12
                                RowLayout { Layout.fillWidth: true
                                    Text { text: 'Prepare a world'; color: '#eef1fa'; font.pixelSize: 20; Layout.fillWidth: true }
                                    Body { text: s.cf_pack.name || 'Choose your server software' }
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
                                RowLayout {
                                    Caption { text: 'TUNNEL EDITION' }
                                    Combo { choices: ['Auto','Java','Bedrock']; currentIndex: choices.indexOf(s.tunnel_type || 'Auto'); onActivated: nova.update('tunnel_type',currentText) }
                                    Body { text: 'Java = TCP · Bedrock = UDP. Select the matching server edition.'; Layout.fillWidth: true }
                                }
                                Body { text: 'Switching replaces the whole folder. Backups happen only when you click Manual backup.'; Layout.fillWidth: true }
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
                // MODPACKS
                Item { ColumnLayout {
                    anchors.fill: parent; anchors.margins: 26; spacing: 14
                    Heading { text: 'Find your next adventure.' }
                    RowLayout { Layout.fillWidth: true
                        Field { id: api; placeholderText: 'CurseForge API key — saved encrypted on this PC'; text: nova.apiKey; echoMode: TextInput.Password; Layout.fillWidth: true; onTextEdited: nova.update('apiKey',text); onEditingFinished: nova.saveApiKey() }
                        Action { text: 'Forget key'; onClicked: nova.forgetApiKey() }
                        Action { text: 'API access'; onClicked: Qt.openUrlExternally('https://support.curseforge.com/support/solutions/articles/9000208346-about-the-curseforge-api-and-how-to-apply-for-a-key') }
                    }
                    RowLayout { Layout.fillWidth: true
                        Field { id: search; placeholderText: 'Search modpacks…'; Layout.fillWidth: true; onAccepted: nova.query(text,sort.currentText,mc.text,0) }
                        Combo { id: sort; choices: ['Popular','Relevant','Recently updated','Most downloaded']; onActivated: nova.query(search.text,currentText,mc.text,0) }
                        Field { id: mc; placeholderText: 'MC version'; Layout.preferredWidth: 100 }
                        BusyAction { text: 'Search'; primary: true; onClicked: nova.query(search.text,sort.currentText,mc.text,0) }
                    }
                    RowLayout { Layout.fillWidth: true; Layout.fillHeight: true; spacing: 18
                        GridView { id: gallery; Layout.fillWidth: true; Layout.fillHeight: true; clip: true; cellWidth: Math.floor(width/2); cellHeight: 222; model: s.packs
                            delegate: Item { required property var modelData; required property int index; width: gallery.cellWidth; height: 222
                                Panel { anchors.fill: parent; anchors.rightMargin: 10; anchors.bottomMargin: 10
                                    ColumnLayout { anchors.fill: parent; anchors.margins: 15; spacing: 8
                                        Image { source: (modelData.logo || {}).thumbnailUrl || ''; asynchronous: true; fillMode: Image.PreserveAspectFit; Layout.fillWidth: true; Layout.preferredHeight: 96 }
                                        Text { text: modelData.name; color: '#edf1f9'; font.pixelSize: 15; font.weight: Font.DemiBold; elide: Text.ElideRight; Layout.fillWidth: true }
                                        Body { text: Math.round(modelData.downloadCount).toLocaleString()+' downloads'; font.pixelSize: 11 }
                                        BusyAction { text: 'View pack'; implicitHeight: 30; Layout.fillWidth: true; onClicked: nova.project(index,0) }
                                    }
                                }
                            }
                        }
                        Panel { Layout.preferredWidth: 330; Layout.fillHeight: true
                            ScrollView { id: detail; anchors.fill: parent; anchors.margins: 18; contentWidth: availableWidth; clip: true
                                ColumnLayout { width: detail.availableWidth; spacing: 12
                                    Text { text: s.project.name || 'A world of possibilities'; color: '#f1f3fa'; font.pixelSize: 22; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                                    Body { text: s.project.summary || 'Enter your API key, load popular packs, then select a pack to inspect its releases and mods.'; Layout.fillWidth: true }
                                    Combo { choices: s.releases.map(r=>(r.displayName || r.fileName)+' / Server: '+(r.serverPackFileId ? 'Yes' : 'No')); currentIndex: s.releaseIndex; Layout.fillWidth: true; onActivated: nova.update('releaseIndex',currentIndex) }
                                    BusyAction { text: 'Use selected release'; primary: true; Layout.fillWidth: true; enabled: s.releases.length>0 && !s.busy; onClicked: { nova.action('pick'); win.page=1 } }
                                    RowLayout {
                                        BusyAction { text: 'Older releases'; enabled: !!s.project.id && !s.busy; onClicked: nova.action('older') }
                                        Action { text: 'Pack website'; enabled: !!s.project.links; onClicked: Qt.openUrlExternally(s.project.links.websiteUrl) }
                                    }
                                    BusyAction { text: 'View release mod list'; Layout.fillWidth: true; enabled: s.releases.length>0 && !s.busy; onClicked: nova.action('mods') }
                                    Body { text: 'Mod list comes from the client manifest. Server pack contents may differ.'; Layout.fillWidth: true; font.pixelSize: 11 }
                                    Field { id: modSearch; placeholderText: 'Filter mods…'; Layout.fillWidth: true }
                                    Repeater { model: s.mods.filter(m=>m.name.toLowerCase().includes(modSearch.text.toLowerCase()))
                                        RowLayout { required property var modelData; Layout.fillWidth: true
                                            Image { source: modelData.logo || ''; asynchronous: true; Layout.preferredWidth: 32; Layout.preferredHeight: 32; fillMode: Image.PreserveAspectFit }
                                            Body { text: modelData.name; Layout.fillWidth: true }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    RowLayout {
                        BusyAction { text: 'Previous'; enabled: s.pageIndex>=20 && !s.busy; onClicked: nova.query(search.text,sort.currentText,mc.text,s.pageIndex-20) }
                        BusyAction { text: 'Next'; enabled: s.packs.length===20 && !s.busy; onClicked: nova.query(search.text,sort.currentText,mc.text,s.pageIndex+20) }
                        Body { text: 'Relevant ranks names within the current results page. API key saves encrypted for your Windows account.'; Layout.fillWidth: true }
                    }
                }
                }
                // FILES
                Item { ColumnLayout {
                    anchors.fill: parent; anchors.margins: 26; spacing: 14
                    RowLayout { Heading { text: 'Shape your world.'; Layout.fillWidth: true } BusyAction { text: 'Save All'; primary: true; enabled: s.filesLoaded && s.server==='Stopped' && !s.busy; onClicked: nova.action('save_all') } BusyAction { text: 'Reload files'; onClicked: nova.action('files') } }
                    Body { text: 'Core server files load automatically. New installations are saved and ready; Save All or Ctrl+S saves your file and server settings edits.'; Layout.fillWidth: true }
                    Body { visible: !s.filesLoaded; text: 'Install a server or choose its folder on Server to load editable settings.'; Layout.fillWidth: true }
                    TabBar { id: fileTabs; onCurrentIndexChanged: { if(currentIndex===4) nova.action('backups') } objectName: 'fileTabs'; Layout.fillWidth: true; background: Rectangle { color: 'transparent' }
                        NTab { text: 'Configuration editor' } NTab { text: 'Server settings' } NTab { text: 'Mods & plugins' } NTab { text: 'Import ZIP' } NTab { text: 'Backups' }
                    }
                    StackLayout { currentIndex: fileTabs.currentIndex; Layout.fillWidth: true; Layout.fillHeight: true
                        ColumnLayout {
                            RowLayout { Layout.fillWidth: true
                                Combo { id: configs; choices: s.files; Layout.fillWidth: true; onActivated: nova.open_file(currentText) }
                                Action { text: 'Open / reload'; onClicked: nova.open_file(configs.currentText) }
                                BusyAction { text: 'Save file'; primary: true; onClicked: nova.action('write') }
                            }
                            Body { text: (s.file || 'Select a file')+(s.dirty ? '  • Unsaved changes' : '') }
                            ScrollView { Layout.fillWidth: true; Layout.fillHeight: true; clip: true
                                TextArea { id: editor; property bool syncing: false
                                    function syncText() { if (text!==s.editor) { syncing=true; text=s.editor; syncing=false } }
                                    Component.onCompleted: syncText()
                                    Connections { target: nova; function onChanged() { editor.syncText() } }
                                     color: '#d5dfef'; font.family: 'Consolas'; font.pixelSize: 13; selectByMouse: true; wrapMode: TextEdit.NoWrap; background: Rectangle { color: '#10141c'; radius: 12 } onTextChanged: { if(!syncing && text!==s.editor) nova.update('editor',text) } }
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
                            Body { text: 'Import a downloaded server ZIP. All existing server files will be replaced. Make a manual backup first if you want to keep your world.'; Layout.fillWidth: true }
                            Field { text: s.archive || ''; placeholderText: 'Path to server ZIP in Downloads'; Layout.fillWidth: true; onEditingFinished: nova.setPath('archive',text) }
                            Field { text: s.archiveUrl || ''; placeholderText: 'Or paste a direct HTTPS server ZIP link'; Layout.fillWidth: true; onTextEdited: nova.setPath('archiveUrl',text) }
                            BusyAction { text: 'Scan Downloads'; onClicked: nova.action('downloads') }
                            Combo { choices: s.downloads || []; Layout.fillWidth: true; onActivated: nova.setPath('archive',currentText) }
                            BusyAction { text: 'Select ZIP'; onClicked: nova.browse('archive') }
                            BusyAction { text: 'Replace from ZIP'; primary: true; onClicked: nova.action('zip') }
                            Item { Layout.fillHeight: true }
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
                        Panel { Layout.fillWidth: true; implicitHeight: updateColumn.implicitHeight+40
                            ColumnLayout { id: updateColumn; anchors.fill: parent; anchors.margins: 20; spacing: 12
                                Caption { text: 'NOVA UPDATES · '+s.appVersion }
                                Body { text: s.updateStatus || ''; Layout.fillWidth: true }
                                RowLayout {
                                    Action { objectName: 'checkUpdatesButton'; text: 'Check for updates'; enabled: !s.updateBusy && !s.exiting; onClicked: nova.action('check_updates') }
                                    Action { text: 'Download update'; visible: !!s.updateAvailable && !s.updateReady; enabled: !s.updateBusy && !s.exiting; onClicked: nova.action('download_update') }
                                    Action { text: 'Install update'; visible: !!s.updateReady; primary: true; enabled: !s.updateBusy && !s.exiting; onClicked: nova.action('install_update') }
                                }
                                Body { text: 'Checks include public beta releases. Downloads are verified against the release SHA-256 checksum. Stop all servers and tunnels before installing. Updates never install automatically.'; Layout.fillWidth: true }
                                Body { visible: !!s.updateAvailable; text: s.updateNotes || ''; textFormat: Text.PlainText; Layout.fillWidth: true; maximumLineCount: 12; elide: Text.ElideRight }
                            }
                        }

                        Body { text: 'Connection preferences save automatically. Passwords and passphrases stay in memory. CurseForge keys save encrypted for your Windows account.'; Layout.fillWidth: true }
                        Panel { Layout.fillWidth: true; implicitHeight: storageColumn.implicitHeight+40
                            ColumnLayout { id: storageColumn; anchors.fill: parent; anchors.margins: 20; spacing: 12
                                Caption { text: 'MAIN SERVERS FOLDER' }
                                RowLayout { Layout.fillWidth: true
                                    Field { objectName: 'serversRootField'; text: nova.serversRoot; Layout.fillWidth: true; onEditingFinished: nova.setServersRoot(text) }
                                    BusyAction { text: 'Choose folder'; onClicked: nova.chooseServersRoot() }
                                }
                                Body { text: 'Choose this once. + Add automatically creates a named subfolder for each new server. Duplicate names get a number. Install / switch fills that folder with the server files. Existing worlds keep their current locations.'; Layout.fillWidth: true }
                            }
                        }
                        Panel { Layout.fillWidth: true; implicitHeight: connectionColumn.implicitHeight+40
                            ColumnLayout { id: connectionColumn; anchors.fill: parent; anchors.margins: 20; spacing: 12
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
                        Panel { Layout.fillWidth: true; implicitHeight: portColumn.implicitHeight+40
                            ColumnLayout { id: portColumn; anchors.fill: parent; anchors.margins: 20; spacing: 12
                                Caption { text: 'VPS PORT RANGES' }
                                Body { text: 'Allow extra public ports in advance. Use inclusive ranges or commas, e.g. 25565-25575, 25580. Leave blank to allow only assigned profile ports. Up to 256 additional ports per protocol.'; Layout.fillWidth: true }
                                Repeater { model: [{key:'java_port_ranges',label:'Java TCP range',example:'25565-25575'},{key:'bedrock_port_ranges',label:'Bedrock UDP range',example:'19132-19142'}]
                                    RowLayout { required property var modelData; Layout.fillWidth: true
                                        Body { text: modelData.label; Layout.preferredWidth: 190 }
                                        Field { objectName: modelData.key+'Field'; text: s[modelData.key] || ''; placeholderText: modelData.example; Layout.fillWidth: true; enabled: !s.busy; onTextEdited: nova.draft(modelData.key,text); onEditingFinished: nova.update(modelData.key,text) }
                                    }
                                }
                                Body { text: 'Save preferences, then Configure VPS to apply SSH and active UFW permissions. Existing profile ports stay included. New profiles inherit these ranges and take a free public port. Each server still listens on one port. Provider firewalls must allow the same ranges.'; Layout.fillWidth: true }
                                Caption { text: 'PROFILE GAME PORTS' }
                                Body { text: 'Each simultaneous server needs its own folder and local ports. Profiles on the same VPS also need unique public ports. Run Configure VPS after adding profiles or changing public ports.'; Layout.fillWidth: true }
                                Repeater { model: [{key:'local_java_port',label:'Java local TCP'},{key:'remote_java_port',label:'Java public TCP'},{key:'local_bedrock_port',label:'Bedrock local UDP'},{key:'bedrock_ipv6_port',label:'Bedrock local IPv6 UDP'},{key:'remote_bedrock_port',label:'Bedrock public UDP'}]
                                    RowLayout { required property var modelData; Layout.fillWidth: true
                                        Body { text: modelData.label; Layout.preferredWidth: 190 }
                                        Field { objectName: modelData.key+'Field'; text: String(s[modelData.key]); enabled: s.server==='Stopped' && !s.busy; Layout.fillWidth: true; onTextEdited: nova.draft(modelData.key,text); onEditingFinished: nova.update(modelData.key,text) }
                                    }
                                }
                            }
                        }
                        Panel { Layout.fillWidth: true; implicitHeight: dnsColumn.implicitHeight+40
                            ColumnLayout { id: dnsColumn; anchors.fill: parent; anchors.margins: 20; spacing: 12
                                Caption { text: 'DOMAIN & DISPLAY' }
                                Body { text: 'At IONOS, create an A record for '+(s.join_address || 'your game domain')+' pointing to '+(s.vps_host || 'your VPS IPv4 address')+'. Use @ for the root domain. TTL of 1 hour is fine. If using Cloudflare, select DNS only. Changes here do not update DNS.'; Layout.fillWidth: true }
                                Body { text: 'Java TCP: '+s.remote_java_port+'   •   Bedrock UDP: '+s.remote_bedrock_port+'\nVPS setup needs root or passwordless sudo. Allow every profile’s public port in provider firewalls.'; Layout.fillWidth: true }
                                Switch { text: 'Reduce motion'; checked: s.reduced; palette.windowText: '#c0c8d8'; onToggled: nova.update('reduced',checked) }
                                Body { text: 'Closing the window keeps hosting in the tray. Right-click Nova’s tray icon and choose Exit Nova to save the world and stop its processes.'; Layout.fillWidth: true }
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
        if(!s.reduced) fade.restart()
        if(win.page===3) nova.action('ensure_files')
    }
    ParallelAnimation { id: fade
        NumberAnimation { target: pages; property: 'opacity'; from: 0.25; to: 1; duration: 240; easing.type: Easing.OutCubic }
        NumberAnimation { target: pages; property: 'revealOffset'; from: 18; to: 0; duration: 300; easing.type: Easing.OutCubic }
    }
    Connections { target: nova
        function onChanged() {
            const selected=s.profileIndex || 0
            if(selected!==win.shownProfileIndex) {
                win.shownProfileIndex=selected
                if(!s.reduced) fade.restart()
            }
            if(s.reduced) { fade.stop(); pages.opacity=1; pages.revealOffset=0 }
        }
    }
}
