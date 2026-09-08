"""Prepare portable PBR maps from reference-derived albedo images."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'web/public/gallery/flagship/materials'
OUT.mkdir(parents=True, exist_ok=True)

def maps(name, image, roughness, strength):
    image.save(OUT / (name + '-color.jpg'), quality=94)
    gray = np.asarray(image.convert('L'), dtype=float) / 255
    smoothed = np.asarray(image.convert('L').filter(ImageFilter.GaussianBlur(2)), dtype=float) / 255
    height = gray - smoothed
    dx = (np.roll(height,-1,1)-np.roll(height,1,1))*strength
    dy = (np.roll(height,-1,0)-np.roll(height,1,0))*strength
    normal = np.stack([-dx, dy, np.ones_like(dx)], axis=2)
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    Image.fromarray(np.uint8((normal*.5+.5)*255)).save(OUT/(name+'-normal.png'))
    Image.fromarray(np.uint8(np.clip(roughness+height*.3,0,1)*255)).save(OUT/(name+'-roughness.png'))

for name, roughness in [('teak',.62),('walnut',.48)]:
    source = ROOT / 'artifacts/gallery/reference' / name / (name+'.png')
    image = Image.open(source).convert('RGB').resize((1024,1024), Image.Resampling.LANCZOS)
    maps(name,image,roughness,1.7)

rng = np.random.default_rng(61)
noise = np.asarray(Image.fromarray(rng.integers(0,256,(64,64),dtype=np.uint8)).resize((512,512),Image.Resampling.BICUBIC),dtype=float)/255
grain = rng.normal(0,.012,(512,512))
color = np.clip(np.stack([.60+noise*.2+grain,.41+noise*.18+grain,.16+noise*.10+grain],axis=2),0,1)
maps('brass',Image.fromarray(np.uint8(color*255)),.38,1.1)
yy,xx=np.indices((512,512))
fibers=.87+.025*np.sin(xx*np.pi/2)+.025*np.sin(yy*np.pi/2)+grain
color=np.clip(np.stack([fibers,fibers*.95,fibers*.82],axis=2),0,1)
maps('canvas',Image.fromarray(np.uint8(color*255)),.92,1.0)
(OUT/'provenance.json').write_text(json.dumps({'wood_albedo':'image2-api reference edit from approved perspective', 'normal_and_roughness':'Estimated microstructure from albedo, not measured scan data', 'brass_and_canvas':'Deterministic procedural bitmap microstructure, seed 61'},indent=2),encoding='utf-8')
print('PBR maps ready:',OUT)
