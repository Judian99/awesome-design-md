#!/usr/bin/env python3
import concurrent.futures, subprocess, tempfile, json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageStat
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'examples/style-slides'
PREVIEW=OUT/'_previews'
PREVIEW.mkdir(exist_ok=True)
manifest=json.loads((OUT/'manifest.json').read_text())
force='--force' in sys.argv

def render(item):
    slug=item['slug']; target=PREVIEW/f'{slug}.png'
    if target.exists() and not force:
        return slug,True,'cached'
    with tempfile.TemporaryDirectory(prefix='slide-chrome-') as profile:
        cmd=['google-chrome','--headless','--no-sandbox','--disable-gpu','--hide-scrollbars','--force-device-scale-factor=1',f'--user-data-dir={profile}','--window-size=960,540','--virtual-time-budget=700',f'--screenshot={target}',(OUT/item['file']).resolve().as_uri()+'?embed=1#1']
        try:
            r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=45)
            if r.returncode or not target.exists():
                return slug,False,r.stderr[-500:]
            with Image.open(target) as im:
                if im.size!=(960,540): return slug,False,f'bad size {im.size}'
                stat=ImageStat.Stat(im.convert('RGB').resize((96,54)))
                if sum(stat.var)<20: return slug,False,'blank preview'
            return slug,True,f'{target.stat().st_size} bytes'
        except Exception as e:
            return slug,False,str(e)

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results=list(pool.map(render,manifest))
for slug,ok,detail in results:
    print(('OK' if ok else 'FAIL'),slug,detail,flush=True)
failed=[x for x in results if not x[1]]
print(f'Rendered {len(results)-len(failed)}/{len(results)} previews',flush=True)
if failed: raise SystemExit(1)
