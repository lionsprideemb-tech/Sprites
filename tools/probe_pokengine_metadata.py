from pathlib import Path
import urllib.request,re
urls=[
 "https://pokengine.org/collections/10o0ctrn/Mikitari?forms",
 "https://pokengine.org/collections/10o0ctrn/Mikitari",
]
out=[]
for url in urls:
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 MercurySpriteRecovery/1.0"})
    try:
      with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read().decode("utf-8","replace")
      out.append("\n===== "+url+" =====\n")
      for line in raw.splitlines():
        if any(k.lower() in line.lower() for k in ["basculin","basstile","buneary","castform","oricorio","cabat","floramona","duntesert"]):
          out.append(re.sub(r"\s+"," ",line).strip()[:8000]+"\n")
      out.append("\nHREFS\n")
      for href in re.findall(r'href=[\'\"]([^\'\"]+)',raw):
        if any(k in href.lower() for k in ["basculin","basstile","buneary","castform","oricorio","cabat","floramona","duntesert"]):
          out.append(href+"\n")
    except Exception as e: out.append("ERROR "+repr(e)+"\n")
Path("DS_CUSTOM_LIBRARY/DS_READY_MASTER/pokengine_probe.txt").write_text("".join(out),encoding="utf-8")
print("done")
