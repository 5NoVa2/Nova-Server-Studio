from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[1];folder=root/'store/Assets';folder.mkdir(exist_ok=True)
with Image.open(root/'app/Nova.ico') as source:
 source=source.convert('RGBA')
 for name,size in [('StoreLogo',(50,50)),('Square44x44Logo',(44,44)),('Square150x150Logo',(150,150)),('Wide310x150Logo',(310,150)),('Square310x310Logo',(310,310))]:
  canvas=Image.new('RGBA',size,'#090b10');icon=source.copy();icon.thumbnail((int(size[0]*0.88),int(size[1]*0.88)),Image.Resampling.LANCZOS)
  canvas.alpha_composite(icon,((size[0]-icon.width)//2,(size[1]-icon.height)//2));canvas.convert('RGB').save(folder/(name+'.png'))
print('Generated Store tile artwork')
