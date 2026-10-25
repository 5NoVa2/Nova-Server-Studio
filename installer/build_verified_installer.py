"""Compile to an isolated path; validate NSIS length and CRC before promotion."""
import argparse,os,struct,subprocess,sys,tempfile,zlib
from pathlib import Path


def verify(path):
 data=Path(path).read_bytes()
 marker=b'\xef\xbe\xad\xdeNullsoftInst'
 position=data.find(marker)-4
 if position<512 or position+28>len(data):raise ValueError('Missing NSIS header')
 following=struct.unpack_from('<I',data,position+24)[0]
 if position+following!=len(data):raise ValueError('Truncated or oversized NSIS installer')
 if zlib.crc32(data[512:-4])!=struct.unpack_from('<I',data,len(data)-4)[0]:raise ValueError('Installer CRC mismatch')
 return len(data)


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--makensis',default='makensis');args=parser.parse_args()
 root=Path(__file__).resolve().parent;dist=root.parent/'dist';dist.mkdir(exist_ok=True)
 # A second build must not rewrite the shared generated script concurrently.
 lock=dist/'.installer-build-lock'
 try:lock.mkdir()
 except FileExistsError:raise SystemExit('An installer build is already running. Finish it before retrying.')
 try:
  subprocess.run([sys.executable,str(root/'build_installer.py')],check=True)
  with tempfile.TemporaryDirectory(prefix='.verified-build-',dir=dist) as tmp:
   output=Path(tmp)/'SaturnSetup-Private.exe'
   subprocess.run([args.makensis,'-WX','-V2','-DSETUP_OUTPUT='+str(output),str(root/'SaturnSetup.nsi')],check=True)
   size=verify(output)
   os.replace(output,dist/'SaturnSetup.exe')
   print('Verified NSIS length and CRC:',size,'bytes')
 finally:lock.rmdir()

if __name__=='__main__':main()
