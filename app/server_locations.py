"""Safe readable, collision-free child folders for new server profiles."""
import re
from pathlib import Path


def folder_name(name):
    value=re.sub(r'[<>:"/\\|?*\x00-\x1f]','-',name)
    value=re.sub(r'\s+',' ',value).strip(' .')[:64].rstrip(' .') or 'Server'
    stem=value.split('.',1)[0].strip(' .').upper()
    if stem in {'CON','PRN','AUX','NUL'} or re.fullmatch(r'(COM|LPT)[1-9]',stem):value='Server '+value
    return value


def new_server_folder(root,name,reserved=()):
    root=Path(root).expanduser().resolve()
    if root.exists() and not root.is_dir():raise ValueError('Choose a folder for server storage, not a file.')
    if (root/'server.properties').exists():raise ValueError('Choose a parent folder, not an existing Minecraft server folder.')
    occupied={str(Path(p).expanduser().resolve()).casefold() for p in reserved}
    if root.exists():occupied.update(str(p.resolve()).casefold() for p in root.iterdir())
    base=folder_name(name);number=1
    while True:
        candidate=root/(base if number==1 else base+' '+str(number))
        if not candidate.exists() and str(candidate).casefold() not in occupied:
            from app import validate_server_folder
            validate_server_folder(candidate)
            root.mkdir(parents=True,exist_ok=True)
            try:candidate.mkdir(exist_ok=False)
            except FileExistsError:number+=1;continue
            return candidate
        number+=1
