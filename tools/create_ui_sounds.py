"""Original quiet, short UI effects; no external samples or runtime dependencies."""
import math,random,struct,wave
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'app/sounds';rate=48000
for kind,duration in [('hover',0.045),('click',0.24),('transition',0.18)]:
 rng=random.Random(31);samples=[];low=0.0
 for i in range(int(rate*duration)):
  t=i/rate;noise=rng.uniform(-1,1);low+=0.18*(noise-low)
  if kind=='hover':v=math.sin(2*math.pi*1550*t)*math.exp(-t*115)*min(1,t/0.003)
  elif kind=='click':
   # Rounded sine ping: gentle onset, no noise transient, faint orbital overtone.
   envelope=(1-math.exp(-t/0.014))**2*math.exp(-t/0.052)
   v=(math.sin(2*math.pi*659.25*t)+0.10*math.sin(2*math.pi*988.88*t))*envelope
  else:v=(math.sin(2*math.pi*392*t)+0.12*math.sin(2*math.pi*588*t))*math.sin(math.pi*t/duration)**2
  samples.append(v*min(1,(duration-t)/0.01))
 scale=(0.26 if kind=='click' else 0.20 if kind=='transition' else 0.45)/max(abs(v) for v in samples)
 with wave.open(str(root/(kind+'.wav')),'wb') as out:
  out.setnchannels(1);out.setsampwidth(2);out.setframerate(rate);out.writeframes(b''.join(struct.pack('<h',round(v*scale*32767)) for v in samples))
print('Generated hover, click and transition effects')
