"""Generate Saturn's original intro sound using only the Python standard library."""
import math,random,struct,wave
from pathlib import Path
rate=48000;duration=4.75;rng=random.Random(731);samples=[];low=0.0
for n in range(int(rate*duration)):
 t=n/rate
 noise=rng.uniform(-1,1);low+=0.045*(noise-low)
 sweep=math.exp(-((t-1.15)/0.65)**2)
 airy=math.exp(-((t-1.85)/0.45)**2)
 v=0.36*low*sweep+0.015*noise*airy
 v+=0.028*math.sin(2*math.pi*(63*t+9*t*t))*sweep
 # A small glassy resolution as the final logo and lettering appear.
 for offset,freq,gain in [(2.48,523.25,0.065),(2.60,783.99,0.045),(2.73,1046.5,0.024)]:
  u=t-offset
  if u>=0:
   env=(1-math.exp(-u*95))*math.exp(-u*2.4)
   v+=gain*env*(math.sin(2*math.pi*freq*u)+0.16*math.sin(2*math.pi*freq*2.002*u))
 fade=min(1,t/0.15,(duration-t)/0.35)
 samples.append(v*max(0,fade))
peak=max(abs(v) for v in samples);scale=0.55/peak
path=Path(__file__).resolve().parents[1]/'app/sounds/startup.wav'
with wave.open(str(path),'wb') as out:
 out.setnchannels(1);out.setsampwidth(2);out.setframerate(rate)
 out.writeframes(b''.join(struct.pack('<h',round(v*scale*32767)) for v in samples))
print(path)
