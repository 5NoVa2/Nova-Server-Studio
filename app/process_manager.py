"""Track Nova-owned processes and stop their trees on explicit application exit."""
import os
import signal
import subprocess
import threading
import time

_lock=threading.Lock()
_processes=[]
cancelled=threading.Event()
_job=None


def check_cancelled():
    if cancelled.is_set():raise RuntimeError('Operation canceled because Nova is exiting.')


def _windows_job():
    global _job
    if _job is not None:return _job
    import ctypes
    from ctypes import wintypes as w
    class Basic(ctypes.Structure):
        _fields_=[('PerProcessUserTimeLimit',ctypes.c_int64),('PerJobUserTimeLimit',ctypes.c_int64),('LimitFlags',w.DWORD),('MinimumWorkingSetSize',ctypes.c_size_t),('MaximumWorkingSetSize',ctypes.c_size_t),('ActiveProcessLimit',w.DWORD),('Affinity',ctypes.c_size_t),('PriorityClass',w.DWORD),('SchedulingClass',w.DWORD)]
    class IO(ctypes.Structure):
        _fields_=[(name,ctypes.c_uint64) for name in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
    class Extended(ctypes.Structure):
        _fields_=[('BasicLimitInformation',Basic),('IoInfo',IO),('ProcessMemoryLimit',ctypes.c_size_t),('JobMemoryLimit',ctypes.c_size_t),('PeakProcessMemoryUsed',ctypes.c_size_t),('PeakJobMemoryUsed',ctypes.c_size_t)]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateJobObjectW.argtypes=[ctypes.c_void_p,w.LPCWSTR];kernel.CreateJobObjectW.restype=w.HANDLE
    kernel.SetInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD];kernel.SetInformationJobObject.restype=w.BOOL
    kernel.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE];kernel.AssignProcessToJobObject.restype=w.BOOL
    kernel.CloseHandle.argtypes=[w.HANDLE];kernel.CloseHandle.restype=w.BOOL
    handle=kernel.CreateJobObjectW(None,None)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    info=Extended();info.BasicLimitInformation.LimitFlags=0x2000  # KILL_ON_JOB_CLOSE
    if not kernel.SetInformationJobObject(handle,9,ctypes.byref(info),ctypes.sizeof(info)):
        error=ctypes.get_last_error();kernel.CloseHandle(handle);raise ctypes.WinError(error)
    _job=(kernel,handle)
    return _job


def managed_popen(*args,**kwargs):
    check_cancelled()
    if os.name!='nt':kwargs.setdefault('start_new_session',True)
    # Serialize creation/registration with shutdown so a just-started child is
    # either registered or rejected, never missed by the exit sweep.
    with _lock:
        check_cancelled()
        proc=subprocess.Popen(*args,**kwargs)
        if not hasattr(proc,'pid'):return proc  # lightweight test doubles
        assigned=False
        if os.name=='nt':
            try:
                kernel,handle=_windows_job()
                assigned=bool(kernel.AssignProcessToJobObject(handle,int(proc._handle)))
            except (OSError,AttributeError):pass
        _processes.append((proc,assigned))
        return proc


def stop_all():
    global _job
    cancelled.set()
    with _lock:
        processes=list(_processes);job=_job;_job=None
    if job:
        # Closing the job kills its remaining members and all inherited children.
        job[0].CloseHandle(job[1])
    for proc,assigned in processes:
        if os.name=='nt':
            if assigned:continue
            if proc.poll() is None:
                try:subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=8)
                except (OSError,subprocess.TimeoutExpired):
                    try:proc.kill()
                    except OSError:pass
        else:
            try:os.killpg(proc.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            except OSError:
                try:proc.terminate()
                except OSError:pass
    for proc,assigned in processes:
        try:proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                if os.name!='nt':os.killpg(proc.pid,signal.SIGKILL)
                else:proc.kill()
            except OSError:pass
        except OSError:pass

_workers=set()


def start_worker(function):
    def run():
        try:function()
        finally:
            with _lock:_workers.discard(threading.current_thread())
    thread=threading.Thread(target=run,daemon=True)
    with _lock:
        check_cancelled();_workers.add(thread);thread.start()
    return thread


def wait_workers(timeout):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        with _lock:workers=list(_workers)
        if not workers:return True
        for thread in workers:thread.join(timeout=min(.2,max(0,deadline-time.monotonic())))
    with _lock:return not _workers


def copy_file(source,destination):
    import shutil
    check_cancelled()
    with open(source,'rb') as src,open(destination,'wb') as dst:
        while True:
            check_cancelled();data=src.read(1024*1024)
            if not data:break
            dst.write(data)
    shutil.copystat(source,destination)
    return destination
