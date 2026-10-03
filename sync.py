# §6.1: источник → WebP ≤256px (цель ≤10КБ) → имя по slug (immutable: уже скачанное не трогаем)
import json, os, io, sys, time, urllib.request
from PIL import Image
SRC = os.environ.get('SRC', 'https://raw.githubusercontent.com/jethubvideo-code/gifttracker-bot/main/docs/images.json')
def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': 'gm-mirror'})
    return urllib.request.urlopen(req, timeout=timeout).read()
data = json.loads(fetch(SRC).decode())
imgs = data.get('images') or {}
os.makedirs('docs/img', exist_ok=True)
manifest, fail = {}, []
for slug, url in imgs.items():
    if not url: continue
    dst = 'docs/img/%s.webp' % slug
    if os.path.exists(dst):
        manifest[slug] = 'img/%s.webp' % slug
        continue
    for attempt in range(3):
        try:
            im = Image.open(io.BytesIO(fetch(url))).convert('RGBA')
            if max(im.size) > 256:
                sc = 256 / max(im.size)
                im = im.resize((max(1, int(im.size[0]*sc)), max(1, int(im.size[1]*sc))), Image.LANCZOS)
            for q in (85, 80, 75, 60):
                im.save(dst, 'WEBP', quality=q, method=6)
                if os.path.getsize(dst) <= 10*1024: break
            manifest[slug] = 'img/%s.webp' % slug
            break
        except Exception as e:
            if attempt == 2: fail.append('%s: %s' % (slug, str(e)[:60]))
            time.sleep(2 + attempt*3)
with open('docs/images.json', 'w') as f:
    json.dump({'updated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'images': manifest, 'failed': fail}, f, ensure_ascii=False, indent=1)
print('mirror: %d ok, %d fail, %s' % (len(manifest), len(fail), fail[:5]))
if not manifest and fail and len(fail) >= 50: sys.exit(1)  # тотальный отказ источника
