from pathlib import Path
import urllib.request,re,html as htmlmod,urllib.parse
from html.parser import HTMLParser
class Textify(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self,d):
        d=htmlmod.unescape(d)
        if d.strip(): self.parts.append(d.strip())

queries=["Hayog","Flambafee","Atlasbell","Anuf","Bombustoad"]
out=[]
for q in queries:
    for url in [
        "https://pokengine.org/search?query="+urllib.parse.quote(q),
        "https://pokengine.org/mons?query="+urllib.parse.quote(q),
    ]:
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 MercurySpriteRecovery/1.0"})
            with urllib.request.urlopen(req,timeout=30) as r:
                raw=r.read().decode("utf-8","replace")
            links=re.findall(r"href=['\"](/mons/[^'\"?#]+)",raw)
            p=Textify();p.feed(raw)
            out.append("\n===== "+url+" =====\nSTATUS OK\n")
            out.append("LINKS\n"+"\n".join(dict.fromkeys(links))+"\n")
            out.append("TEXT\n"+"\n".join(p.parts[:250])+"\n")
        except Exception as e:
            out.append("\n===== "+url+" =====\nERROR "+repr(e)+"\n")
Path("DS_CUSTOM_LIBRARY/DS_READY_MASTER/pokengine_probe.txt").write_text("".join(out),encoding="utf-8")
print("wrote search probe")
