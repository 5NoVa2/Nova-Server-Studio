"""Manual backup discovery and staged restoration; no scheduled backups."""
import shutil,tempfile,uuid
from pathlib import Path
from app import validate_server_folder
from process_manager import check_cancelled,copy_file


def list_backups(target):
    target=Path(target).expanduser().resolve()
    if not target.parent.exists():return []
    rows=[]
    for source in target.parent.iterdir():
        if source.name.startswith(target.name+'.backup-') and source.is_dir() and not source.is_symlink():
            rows.append({'name':source.name,'path':str(source),'modified':source.stat().st_mtime})
    return sorted(rows,key=lambda row:row['modified'],reverse=True)


def restore_backup(target,source):
    target=validate_server_folder(target);source=Path(source)
    if source.is_symlink() or str(source.resolve()) not in {row['path'] for row in list_backups(target)}:
        raise ValueError('Choose a backup listed for this server.')
    source=source.resolve();validate_server_folder(source)
    for entry in [source,*source.rglob('*')]:
        check_cancelled()
        if entry.is_symlink() or getattr(entry.stat(follow_symlinks=False),'st_file_attributes',0)&1024:
            raise ValueError('Backups with links or junctions cannot be restored.')
    with tempfile.TemporaryDirectory(prefix='.nova-restore-',dir=target.parent) as temp:
        staged=Path(temp)/'server';shutil.copytree(source,staged,copy_function=copy_file)
        check_cancelled();previous=None
        if target.exists():
            previous=target.with_name('.nova-restore-old-'+uuid.uuid4().hex);target.rename(previous)
        try:staged.rename(target)
        except Exception:
            if previous:previous.rename(target)
            raise
        if previous:shutil.rmtree(previous)
    return target
