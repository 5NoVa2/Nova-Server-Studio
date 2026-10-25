"""Low-cost metrics for the owned server process; no extra dependency or process."""
import os
import time


def read_process(process):
    """Return cumulative CPU seconds and resident bytes on Windows."""
    if os.name != 'nt':
        return None
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(name,ctypes.c_size_t) for name in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    times=kernel.GetProcessTimes
    times.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4
    times.restype=wintypes.BOOL
    memory=kernel.K32GetProcessMemoryInfo
    memory.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    memory.restype=wintypes.BOOL
    handle=wintypes.HANDLE(int(process._handle))
    created,exited,kernel_time,user_time=[wintypes.FILETIME() for _ in range(4)]
    counters=Counters();counters.cb=ctypes.sizeof(counters)
    if not times(handle,ctypes.byref(created),ctypes.byref(exited),ctypes.byref(kernel_time),ctypes.byref(user_time)) or not memory(handle,ctypes.byref(counters),counters.cb):
        return None
    ticks=lambda value:(value.dwHighDateTime<<32)|value.dwLowDateTime
    return (ticks(kernel_time)+ticks(user_time))/10_000_000,counters.WorkingSetSize


class ServerStats:
    def __init__(self, reader=read_process, clock=time.monotonic, cores=None):
        self.reader=reader;self.clock=clock;self.cores=max(1,cores or os.cpu_count() or 1)
        self.process=None;self.previous=None;self.last_sample=None
        self.values={'cpuLoad':None,'ramBytes':None}

    def sample(self, process):
        if process is None or process.poll() is not None:
            self.process=None;self.previous=None;self.last_sample=None
            self.values={'cpuLoad':None,'ramBytes':None};return self.values
        if process is not self.process:
            self.process=process;self.previous=None;self.last_sample=None
        now=self.clock()
        if self.last_sample is not None and now-self.last_sample<2:return self.values
        self.last_sample=now
        try:reading=self.reader(process)
        except (OSError,ValueError,AttributeError):reading=None
        cpu=None
        if reading is not None:
            total,memory=reading
            if self.previous is not None:
                elapsed=now-self.previous[0]
                if elapsed>0:cpu=round(max(0,min(100,(total-self.previous[1])/elapsed/self.cores*100)),1)
            self.previous=(now,total)
            self.values={'cpuLoad':cpu,'ramBytes':int(memory)}
        else:
            self.previous=None;self.values={'cpuLoad':None,'ramBytes':None}
        return self.values
