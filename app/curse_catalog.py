"""CurseForge catalog data and thumbnail helpers, separate from Tk widgets."""
import difflib
import json
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen
from process_manager import check_cancelled
from runtime import USER_AGENT

SORTS={'Popular':2,'Recently updated':3,'Most downloaded':6}


def relevant(items,query):
    query=query.casefold().strip()
    if not query:return items
    terms=query.split()
    def rank(item):
        name=item.get('name','').casefold()
        return (name==query,name.startswith(query),query in name,sum(term in name for term in terms),difflib.SequenceMatcher(None,query,name).ratio(),item.get('downloadCount',0))
    return sorted(items,key=rank,reverse=True)


def release_mods(api,project,file):
    with tempfile.TemporaryDirectory(prefix='nova-pack-preview-') as td:
        archive=Path(td)/'release.zip';api.download(project,file,archive)
        with zipfile.ZipFile(archive) as z:
            if 'manifest.json' not in z.namelist():raise ValueError('This release does not include a CurseForge manifest.')
            if z.getinfo('manifest.json').file_size>2*1024**2:raise ValueError('Pack manifest is too large.')
            manifest=json.loads(z.read('manifest.json'))
    files=manifest.get('files',[])
    ids=list(dict.fromkeys(int(item['projectID']) for item in files))
    metadata={}
    for offset in range(0,len(ids),50):
        check_cancelled()
        for item in api.mods(ids[offset:offset+50]):metadata[item['id']]=item
    rows=[]
    for item in files:
        mod=metadata.get(item['projectID'],{})
        rows.append({'project_id':item['projectID'],'file_id':item['fileID'],'name':mod.get('name','Project '+str(item['projectID'])),'authors':', '.join(a['name'] for a in mod.get('authors',[])),'logo':(mod.get('logo') or {}).get('thumbnailUrl',''),'url':mod.get('links',{}).get('websiteUrl',''),'required':item.get('required',True)})
    return sorted(rows,key=lambda row:row['name'].casefold())


def thumbnail(url):
    parsed=urlparse(url)
    if parsed.scheme!='https' or not (parsed.hostname or '').endswith(('.forgecdn.net','.curseforge.com')):
        raise ValueError('Unsupported thumbnail URL.')
    check_cancelled()
    with urlopen(Request(url,headers={'User-Agent':USER_AGENT}),timeout=10) as response:data=response.read(2*1024**2+1)
    if len(data)>2*1024**2:raise ValueError('Thumbnail exceeds 2 MB.')
    return data
