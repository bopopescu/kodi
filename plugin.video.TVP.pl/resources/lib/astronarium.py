# -*- coding: utf-8 -*-
import urllib2
import urlparse
import re

TIMEOUT = 10
BASEURL='http://www.astronarium.pl'

def getUrl(url,proxy={},timeout=TIMEOUT):
    if proxy:
        urllib2.install_opener(
            urllib2.build_opener(
                urllib2.ProxyHandler(proxy)
            )
        )
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:22.0) Gecko/20100101 Firefox/22.0')
    try:
        response = urllib2.urlopen(req,timeout=timeout)
        out = response.read()
        response.close()
    except:
        out='{}'
    return out

def getEpisodes(url='http://www.astronarium.pl/odcinki/'):
    content=getUrl(url)
    out=[]
    items = re.compile('<a href="(/odcinki.*?)"><img src="(.*?)" alt="(.*?)" class="odcinki-lista"></a>').findall(content)
    for item in items:
        href= BASEURL+item[0]
        imgalt = BASEURL+item[1]
        title = fixSC(item[2].split('"')[0])
        out.append({'title':title,'url':href,'img':imgalt})
    return out

def getVideo(url):
    content=getUrl(url)
    out=''
    iframes = re.compile('<iframe (.*?)</iframe>',re.DOTALL).findall(content)
    for frame in iframes:
        src=re.compile('src="(.*?)"').findall(frame)
        src = src[0] if src else ''
        if 'youtube' in src:
            media_id=urlparse.urlparse(src).path.split('/')[-1]
            out = 'plugin://plugin.video.youtube/play/?video_id=' + media_id
    return out

def fixSC(insc):
    insc = insc.replace('&nbsp;','')
    insc = insc.replace('&lt;br/&gt;',' ')
    insc = insc.replace('&quot;','"').replace('&amp;quot;','"')
    insc = insc.replace('&oacute;','ó').replace('&Oacute;','Ó')
    insc = insc.replace('&amp;oacute;','ó').replace('&amp;Oacute;','Ó')
    insc = insc.replace('\u0105','ą').replace('\u0104','Ą')
    insc = insc.replace('\u0107','ć').replace('\u0106','Ć')
    insc = insc.replace('\u0119','ę').replace('\u0118','Ę')
    insc = insc.replace('\u0142','ł').replace('\u0141','Ł')
    insc = insc.replace('\u0144','ń').replace('\u0144','Ń')
    insc = insc.replace('\u00f3','ó').replace('\u00d3','Ó')
    insc = insc.replace('\u015b','ś').replace('\u015a','Ś')
    insc = insc.replace('\u017a','ź').replace('\u0179','Ź')
    insc = insc.replace('\u017c','ż').replace('\u017b','Ż')
    return insc
