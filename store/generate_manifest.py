"""Generate an MSIX manifest using identity values copied from Partner Center."""
import argparse,re,xml.etree.ElementTree as ET
from pathlib import Path
F='http://schemas.microsoft.com/appx/manifest/foundation/windows10'
U='http://schemas.microsoft.com/appx/manifest/uap/windows10'
R='http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities'
for prefix,uri in [('',F),('uap',U),('rescap',R)]:ET.register_namespace(prefix,uri)

def generate(destination,name,publisher,display,version,preview=False):
 if not re.fullmatch(r'[A-Za-z0-9.-]{3,50}',name):raise ValueError('Use the exact valid Identity Name from Partner Center.')
 if not publisher.startswith('CN=') or '\n' in publisher:raise ValueError('Use the exact Publisher value from Partner Center.')
 parts=version.split('.')
 if len(parts)!=4 or any(not p.isdigit() or int(p)>65535 for p in parts) or int(parts[0])<1:raise ValueError('MSIX version must contain four valid integers.')
 if not preview and (name.endswith('.Preview') or publisher=='CN=SaturnDevelopment'):raise ValueError('Preview identity cannot be used for a Store submission.')
 if parts[-1]!='0':raise ValueError('Reserve the fourth version component as 0 for Store submission.')
 package=ET.Element('Package',{'xmlns':F,'xmlns:uap':U,'xmlns:rescap':R,'IgnorableNamespaces':'uap rescap'})
 ET.SubElement(package,'Identity',Name=name,Publisher=publisher,Version=version,ProcessorArchitecture='x64')
 properties=ET.SubElement(package,'Properties')
 for tag,text in [('DisplayName','Saturn Server Launcher'),('PublisherDisplayName',display),('Logo','Assets/StoreLogo.png')]:ET.SubElement(properties,tag).text=text
 deps=ET.SubElement(package,'Dependencies');ET.SubElement(deps,'TargetDeviceFamily',Name='Windows.Desktop',MinVersion='10.0.19041.0',MaxVersionTested='10.0.26100.0')
 resources=ET.SubElement(package,'Resources');ET.SubElement(resources,'Resource',Language='en-us')
 apps=ET.SubElement(package,'Applications');app=ET.SubElement(apps,'Application',Id='Saturn',Executable='Saturn.exe',EntryPoint='Windows.FullTrustApplication')
 visual=ET.SubElement(app,'uap:VisualElements',DisplayName='Saturn Server Launcher',Description='Manage Minecraft servers on your own PC.',BackgroundColor='#090b10',Square150x150Logo='Assets/Square150x150Logo.png',Square44x44Logo='Assets/Square44x44Logo.png')
 ET.SubElement(visual,'uap:DefaultTile',Wide310x150Logo='Assets/Wide310x150Logo.png',Square310x310Logo='Assets/Square310x310Logo.png')
 caps=ET.SubElement(package,'Capabilities');ET.SubElement(caps,'rescap:Capability',Name='runFullTrust')
 tree=ET.ElementTree(package);ET.indent(tree);destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True);tree.write(destination,encoding='utf-8',xml_declaration=True)
 return destination
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--name',required=True);p.add_argument('--publisher',required=True);p.add_argument('--display',required=True);p.add_argument('--version',default='1.0.17.0');p.add_argument('--preview',action='store_true');a=p.parse_args()
 print(generate(a.output,a.name,a.publisher,a.display,a.version,a.preview))
