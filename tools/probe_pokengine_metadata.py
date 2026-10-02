from pathlib import Path
import urllib.request,re
urls=[
 "https://pokengine.org/collections/10o0ctrn/Mikitari",
 "https://pokengine.org/mons/00iwk4l3/Basstile",
 "https://pokengine.org/mons/001271g9/Bombustoad",
]
out=[]
for url in urls:
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 MercurySpriteRecovery/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        html=r.read().decode("utf-8","replace")
    out.append("\n===== "+url+" =====\n")
    out.append("LEN "+str(len(html))+"\n")
    # Keep only lines likely relevant to mon links, types, evolution, collection cards.
    for line in html.splitlines():
        low=line.lower()
        if any(k in low for k in ["/mons/","type","evol","collection","basstile","bombustoad","troutle","smoald"]):
            line=re.sub(r"\s+"," ",line).strip()
            if line:
                out.append(line[:3000]+"\n")
Path("DS_CUSTOM_LIBRARY/DS_READY_MASTER/pokengine_probe.txt").write_text("".join(out),encoding="utf-8")
print("wrote probe")
