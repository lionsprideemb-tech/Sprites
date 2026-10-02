from pathlib import Path
import urllib.request,re,html as htmlmod
from html.parser import HTMLParser

class Textify(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]
    def handle_data(self,d):
        d=htmlmod.unescape(d)
        if d.strip(): self.parts.append(d.strip())

urls=[
 "https://pokengine.org/collections/10o0ctrn/Mikitari",
 "https://pokengine.org/mons/00iwk4l3/Basstile",
 "https://pokengine.org/mons/001271g9/Bombustoad",
]
out=[]
for url in urls:
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 MercurySpriteRecovery/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read().decode("utf-8","replace")
    p=Textify(); p.feed(raw); txt="\n".join(p.parts)
    out.append("\n===== "+url+" =====\n")
    out.append(txt+"\n")
Path("DS_CUSTOM_LIBRARY/DS_READY_MASTER/pokengine_probe.txt").write_text("".join(out),encoding="utf-8")
print("wrote text probe")
