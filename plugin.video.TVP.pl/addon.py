# -*- coding: utf-8 -*-
import os,sys
import urllib,urllib2
import re,json
import urlparse
import xbmc,xbmcgui,xbmcaddon
import xbmcplugin
import resources.lib.vodTVPapi as vod
import time
import inputstreamhelper

base_url        = sys.argv[0]
addon_handle    = int(sys.argv[1])
args            = urlparse.parse_qs(sys.argv[2][1:])
my_addon        = xbmcaddon.Addon()
vod.my_addon    = my_addon
addonId         = my_addon.getAddonInfo('id')
PATH            = my_addon.getAddonInfo('path')
DATAPATH        = xbmc.translatePath(my_addon.getAddonInfo('profile')).decode('utf-8')
RESOURCES       = PATH+'/resources/'
FAV             = os.path.join(DATAPATH,'favorites.json')
tm              = time.gmtime()

def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link

def getUrlJs(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0')
	response = urllib2.urlopen(req)
	link=json.load(response)	
	response.close()
	return link
def addLinkItem(name, url, mode, iconimage=None, infoLabels=False, IsPlayable=True,fanart=None):
    u = buildUrl({'mode': mode, 'foldername': name, 'ex_link' : url})
    if iconimage==None:
        iconimage='DefaultFolder.png'
    liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setArt({ 'icon' : iconimage})
    if not infoLabels:
        infoLabels={"Title": name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    if IsPlayable:
        liz.setProperty('IsPlayable', 'true')
    if fanart:
        liz.setProperty('fanart_image',fanart)
        liz.setArt({ 'poster': fanart, 'fanart':fanart,'banner':fanart})
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz)
    return ok

def addDir(name,ex_link=None,page=1,mode='folder',contextO=['F_ADD'],iconImage='DefaultFolder.png',fanart=''):
    url = buildUrl({'mode': mode, 'foldername': name, 'ex_link' : ex_link,'page' :page})
    li = xbmcgui.ListItem(name, iconImage=iconImage)
    li.setArt({ 'icon' : iconImage})
    if fanart:
        li.setProperty('fanart_image', fanart )
        li.setArt({ 'poster': fanart, 'fanart':fanart,'banner':iconImage})
    content=urllib.quote_plus(json.dumps({'title':name,'id':ex_link,'img':iconImage}))
    contextMenuItems=[]
    if 'F_ADD' in contextO:
        contextMenuItems.append(('[COLOR lightblue]Dodaj do Wybranych[/COLOR]', 'RunPlugin(plugin://%s?mode=favoritesADD&ex_link=%s)'%(addonId,content)))
    if 'F_REM' in contextO:
        contextMenuItems.append(('[COLOR red]Usuń z Wybranych[/COLOR]', 'RunPlugin(plugin://%s?mode=favoritesREM&ex_link=%s)'%(addonId,content)))
    if 'F_DEL' in contextO:
        contextMenuItems.append(('[COLOR red]Usuń Wszystko[/COLOR]', 'RunPlugin(plugin://%s?mode=favoritesREM&ex_link=all)'%(addonId)))
    li.addContextMenuItems(contextMenuItems, replaceItems=False)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,listitem=li, isFolder=True)

def buildUrl(query):
    return base_url + '?' + urllib.urlencode(query)

def tvp_news(name,URL='http://wiadomosci.tvp.pl/'):
	content = getUrl(URL)
	vido_id = re.compile('data-video-id="(.+?)"', re.DOTALL).findall(content)[0]
	url_player='http://wiadomosci.tvp.pl/sess/tvplayer.php?&object_id=' + vido_id
	content = getUrl(url_player)
	poster_link = re.compile("poster:'(.+?)\'", re.DOTALL).findall(content)
	poster_link = poster_link[0] if poster_link else ''
	title_link = re.compile('title: "(.+?)",', re.DOTALL).findall(content)
	title_link = title_link[0] if title_link else ''
	vido_link = re.compile("1:{src:\'(.+?)\'", re.DOTALL).findall(content)
	
	if not vido_link:
		vido_link = re.compile("0:{src:\'(.+?)\'", re.DOTALL).findall(content)
		if vido_link:
			vido_link = vod.m3u_quality(vido_link[0])
			title_link += ' (Live) '
	if vido_link:
		for vl in vido_link:
			url = vl
			l1base_url = ''
			if isinstance(vl,dict):
				url = vl.get('url',vl)
				l1base_url='[B]'+vl.get('title','')+'[/B]'
			li = xbmcgui.ListItem(name +' ' + title_link + l1base_url, iconImage=poster_link)
			li.setArt({ 'poster': poster_link, 'thumb' : poster_link, 'icon' : poster_link ,'fanart':poster_link,'banner':poster_link})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
	if fname.startswith('Wiadom'):
		addDir('Archiwum Wiadomości',ex_link='30904465',mode='vodTVP',iconImage='https://s.tvp.pl/images/3/7/b/uid_37bb32af5d6a78eb11f0ceb85e2e6ac01447946809413_width_218_play_0_pos_0_gs_0.jpg')
	elif fname.startswith('Telee'):
		addDir('Archiwum Teleexpress',ex_link='30904469',mode='vodTVP',iconImage='https://s.tvp.pl/images/4/1/4/uid_414630010fdb28fba3a1dab5c13d31101448010259841_width_218_play_0_pos_0_gs_0.jpg')
	elif fname.startswith('Panor'):
		addDir('Archiwum Panorama',ex_link='30904475',mode='vodTVP',iconImage='https://s.tvp.pl/images/0/0/6/uid_006933b2d603550f0dc0e8b86bf604751448010129661_width_218_play_0_pos_0_gs_0.jpg')

def get_tvpLiveStreams(url='http://tvpstream.vod.tvp.pl'):
    data=getUrl(url)
    livesrc="http://tvpstream.vod.tvp.pl/sess/tvplayer.php?object_id=%s"
    img = re.compile('data-video-id=[\'"](\d+)[\'"]\s+title=[\'"](.*?)[\'"].*?data-stationname=[\'"](.*?)[\'"].+?<img src=[\'"](.*?)[\'"]',re.DOTALL).findall(data)
    out=[]
    for id,title,channel,imgalt in img:
        out.append({'title':'[B][COLOR orange]'+channel+'[/COLOR][/B]'+' '+title,'img':imgalt,
                    'url':livesrc % id})
    return out

def playLiveVido(ex_link='http://tvpstream.vod.tvp.pl/sess/tvplayer.php?object_id=34832686'):
	id=re.compile('object_id=(\d+)',re.DOTALL).findall(ex_link)[0]
	url = 'http://www.tvp.pl/shared/cdn/tokenizer_v2.php?object_id='+id
	data=getUrlJs(url)
	
	stream_url = ''

	if my_addon.getSetting('inputstream') == 'false':
		for item in data.get('formats', []):
			if item.get('mimeType') == 'application/x-mpegurl':
				stream_url = item.get('url', '')
				break	
		play_item = xbmcgui.ListItem(path=stream_url)
	else:
		for item in data.get('formats', []):
			if item.get('mimeType') == 'application/vnd.ms-ss':
				stream_url = item.get('url', '')
				break			
		is_helper = inputstreamhelper.Helper('ism')
		if is_helper.check_inputstream():
			play_item = xbmcgui.ListItem(path=stream_url)
			play_item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
			play_item.setProperty('inputstream.adaptive.manifest_type', 'ism')
			play_item.setMimeType('application/vnd.ms-ss')
			play_item.setContentLookup(False)
	xbmcplugin.setResolvedUrl(addon_handle, True, play_item)

def vodtvp_Informacje_Publicystyka():
    addDir('Wiadomości',ex_link='22672029',mode='vodTVP',iconImage='https://s.tvp.pl/images/3/7/b/uid_37bb32af5d6a78eb11f0ceb85e2e6ac01447946809413_width_218_play_0_pos_0_gs_0.jpg')
    addDir('Panorama',ex_link='22672017',mode='vodTVP',iconImage='https://s.tvp.pl/images/0/0/6/uid_006933b2d603550f0dc0e8b86bf604751448010129661_width_218_play_0_pos_0_gs_0.jpg')
    addDir('Teleexpress',ex_link='22672041',mode='vodTVP',iconImage='https://s.tvp.pl/images/4/1/4/uid_414630010fdb28fba3a1dab5c13d31101448010259841_width_218_play_0_pos_0_gs_0.jpg')
    addDir('Serwis Info',ex_link='22672079',mode='vodTVP',iconImage='https://s.tvp.pl/images/5/c/3/uid_5c38f1ddddbd576c0d3b3d0de33be6c41448010407181_width_218_play_0_pos_0_gs_0.png')
    addDir('Agrobiznes',ex_link='22672105',mode='vodTVP',iconImage='https://s.tvp.pl/images/b/7/8/uid_b78d8b4658ba508758116242d49d6e6b1448010537460_width_218_play_0_pos_0_gs_0.jpg')
    addDir('Minęła dwudziesta',ex_link='22673971',mode='vodTVP',iconImage='https://s.tvp.pl/images/f/9/1/uid_f91f32e961eb0309182f60146d0799d01448010719625_width_218_play_0_pos_0_gs_0.png')
    addDir('Po prostu. Program Tomasza Sekielskiego',ex_link='9525905',mode='vodTVP',iconImage='')
    addDir('Polityka przy kawie',ex_link='2625476',mode='vodTVP',iconImage='http://s.tvp.pl/images/2/1/7/uid_217cbf307a79ac55e7b5c48389a59b6b1286463046834_width_218_play_0_pos_0_gs_0.jpg')
    addDir('Publicystyka Najnowsze',ex_link='8306415',mode='vodTVP',iconImage='')

def vodtvp_Kabarety_TVP():
    addDir('TOP 10',ex_link='1342039',mode='vodTVP')
    addDir('Skecze',ex_link='883',mode='vodTVP')
    addDir('Festiwale',ex_link='4982024',mode='vodTVP')
    addDir('Teraz Ogladane',ex_link='5264287',mode='vodTVP')
    addDir('Kabaretowy Klub Dwójki',ex_link='4066916',mode='vodTVP')
    addDir('Dzięki Bogu już weekend',ex_link='10237279',mode='vodTVP',iconImage='http://s.tvp.pl/images/b/6/6/uid_b66006e90129a44f228baccebfa295241456936112117_width_218_play_0_pos_0_gs_0.jpg')
    addDir('N jak Neonówka',ex_link='5775029',mode='vodTVP')
    addDir('Kabaretożercy',ex_link='2625743',mode='vodTVP')

def vodtvp_RIO():
    addDir('Transmisje',ex_link='23578493',mode='vodTVP')
    addDir('Wideo',ex_link='23578509',mode='vodTVP')
    addDir('Dyscypliny',ex_link='24035157',mode='vodTVP')

def settings_getProxy():
    protocol =  my_addon.getSetting('protocol')
    ipaddress = my_addon.getSetting('ipaddress')
    ipport = my_addon.getSetting('ipport')
    proxyG = my_addon.getSetting('proxyG')
    if 'http' in protocol and ipport and ipaddress and proxyG=='true':
        return {protocol: '%s:%s'%(ipaddress,ipport)}
    else:
        return {}

def settings_setProxy(proxy={'http':'10.10.10.10:50'}):
    protocol = proxy.keys()[0]
    ipaddress,ipport = proxy[protocol].split(':')
    my_addon.setSetting('protocol',protocol)
    my_addon.setSetting('ipaddress',ipaddress)
    my_addon.setSetting('ipport',ipport)

def ReadJsonFile(jfilename):
    if os.path.exists(jfilename):
        with open(jfilename,'r') as f:
            content = f.read()
            if not content:
                content ='[]'
    else:
        content = '[]'
    data=json.loads(content)
    return data

xbmcplugin.setContent(addon_handle, 'episodes')
my_addon.setSetting('set','set')
mode = args.get('mode', None)
fname = args.get('foldername',[''])[0]
ex_link = args.get('ex_link',[''])[0]
page = args.get('page',['1'])[0]

def getQuality(label,bitrate):
    try:
        quality = int(my_addon.getSetting('quality'))
    except:
        quality=0
    lq = [-2,-1,91000,54200,28500,17500,12500][quality]
    if lq==-1:
        s = len(label)-1
    elif lq in bitrate:
        s = bitrate.index(lq)
    else:
        s = xbmcgui.Dialog().select(u'Wybierz jakość video [albo ustaw automat w opcjach]', label)
    return s

if mode is None:
	a,b=vod.logowanie()
	addDir('Wiadomości','http://wiadomosci.tvp.pl/',mode='_news_',contextO=[],iconImage=RESOURCES+'wiadomosci.png')
	addDir('Teleexpress','http://teleexpress.tvp.pl/',mode='_news_',contextO=[],iconImage=RESOURCES+'teleexpress.png')
	addDir('Panorama','http://panorama.tvp.pl/',mode='_news_',contextO=[],iconImage=RESOURCES+'panorama.png')
	addDir('TVP info Live','http://tvpstream.vod.tvp.pl',contextO=[],iconImage=RESOURCES+'tvp-info.png')
	addDir('Kabarety TVP',ex_link='',mode='_Kabarety',contextO=[],iconImage=RESOURCES+'kabaretytvp.png')
	addDir('Astronarium',ex_link='http://www.astronarium.pl/odcinki/',mode='Astronarium',contextO=[],iconImage='http://www.astronarium.pl/pliki/astronarium_logo_small.jpg')
	addDir('Przegapiłeś w TV',mode='vodTVP_przegapiles',contextO=[],iconImage=RESOURCES+'vodtvp.png')
	addDir('Regionalne',contextO=[],iconImage=RESOURCES+'vodtvp.png')
	addDir('[COLOR blue]vod.TVP.pl[/COLOR]',contextO=[],iconImage=RESOURCES+'vodtvp.png')
	addDir('[COLOR lightblue]vod.Wybrane[/COLOR]',ex_link=FAV, mode='favorites',contextO=[],iconImage=RESOURCES+'wybrane.png')
	xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
	xbmcplugin.endOfDirectory(addon_handle)
elif mode[0] == 'Astronarium':
	import resources.lib.astronarium as astronarium
	out=astronarium.getEpisodes(ex_link)
	for one in out:
		addLinkItem(one['title'], one['url'], 'Astronarium_play', iconimage=one['img'])
	xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
	xbmcplugin.endOfDirectory(addon_handle)
elif mode[0] == 'Astronarium_play':
    import resources.lib.astronarium as astronarium
    src = astronarium.getVideo(ex_link)
    if src:
        xbmcplugin.setResolvedUrl(addon_handle, True, xbmcgui.ListItem(path=src))
    else:
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem(path=''))

elif mode[0] == '_news_':
	tvp_news(fname,ex_link)
	xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
	xbmcplugin.endOfDirectory(addon_handle)
elif mode[0] == '_infoP':
	vodtvp_Informacje_Publicystyka()
	xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
	xbmcplugin.endOfDirectory(addon_handle)
elif mode[0] == '_Kabarety':
	vodtvp_Kabarety_TVP()
	xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
	xbmcplugin.endOfDirectory(addon_handle)
elif mode[0] == 'palyLiveVideo':
    playLiveVido(ex_link)

elif mode[0] == 'favorites':
	jdata = ReadJsonFile(FAV)
	for k in jdata:
		addDir(k.get('title','').title().encode('utf-8'),str(k.get('id','')),mode='vodTVP',contextO=['F_REM','F_DEL'],iconImage=k.get('img',''))
	xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
	xbmcplugin.endOfDirectory(addon_handle)
elif mode[0] == 'favoritesADD':
	jdata = ReadJsonFile(FAV)
	new_item=json.loads(ex_link)
	dodac = [x for x in jdata if new_item['title']== x.get('title','')]
	if dodac:
		xbmc.executebuiltin('Notification([COLOR pink]Już jest w Wybranych[/COLOR], ' + new_item.get('title','').encode('utf-8') + ', 200)')
	else:
		jdata.append(new_item)
		with open(FAV, 'w') as outfile:
			json.dump(jdata, outfile, indent=2, sort_keys=True)
			xbmc.executebuiltin('Notification(Dodano Do Wybranych, ' + new_item.get('title','').encode('utf-8') + ', 200)')
	xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
	xbmcplugin.endOfDirectory(addon_handle)
elif mode[0] == 'favoritesREM':
	if ex_link=='all':
		yes = xbmcgui.Dialog().yesno("??","Usuń wszystkie filmy z Wybranych?")
		if yes:
			debug=1
	else:
		jdata = ReadJsonFile(FAV)
		remItem=json.loads(ex_link)
		to_remove=[]
		for i in xrange(len(jdata)):
			if int(jdata[i].get('id')) == int(remItem.get('id')):
				to_remove.append(i)
		if len(to_remove)>1:
			yes = xbmcgui.Dialog().yesno("??",remItem.get('title'),"Usuń %d pozycji z Wybranych?" % len(to_remove))
		else:
			yes = True
		if yes:
			for i in reversed(to_remove):
				jdata.pop(i)
			with open(FAV, 'w') as outfile:
				json.dump(jdata, outfile, indent=2, sort_keys=True)
	
	xbmc.executebuiltin('XBMC.Container.Refresh')
	xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
	xbmcplugin.endOfDirectory(addon_handle)
elif mode[0]=='vodTVP_play':	
	stream_url = vod.vodTVP_GetStreamUrl(ex_link)
	if 'material_niedostepny' in stream_url:
		if my_addon.getSetting('proxyG')=='true':
			xbmc.executebuiltin('Notification(material_niedostepny, ' + 'szukam przez proxy' + ', 1200)')
			stream_url = vod.vodTVP_GetStreamUrl(ex_link, pgate = True)
	
		if 'material_niedostepny' in stream_url or not stream_url:
			y=xbmcgui.Dialog().yesno("[COLOR orange]Problem[/COLOR]", '[B]Ograniczenia Licencyjne, material jest niedostępny[/B]','Spróbować użyć serwera proxy ??\n[COLOR blue]W opcjach dostępna alternatywna opcja![/COLOR]')
			if y:
				import resources.lib.twork as tw
				stream_url=''
				timeout=  int(my_addon.getSetting('timeout'))
				dialog  = xbmcgui.DialogProgress()
				dialog.create('Szukam darmowych serwerów proxy ...')
				proxies=vod.getProxies()
				proxy = settings_getProxy()
				if proxy:
					proxies.insert(0,proxy)
				dialog.create('Znalazłem %d serwerów proxy'%len(proxies))
				proxies = [tw.Thread(vod.vodTVP_GetStreamUrl, ex_link,proxy,timeout) for proxy in proxies ]
				[i.start() for i in proxies]
				dialog.update(0,'Sprawdzam %d serwery ... '%(len(proxies)))
				while any([i.isAlive() for i in proxies]):
					xbmc.sleep(1000)
					done = [t for t in proxies if not t.isAlive()]
					dialog.update(int(1.0*len(done)/len(proxies)*100),'Sprawdzam, negatywnie odpowiedziało: %d, proszę czekać'%(len(done)))
					for t in done:
						stream_url = t.result
						if isinstance(stream_url,list) or (stream_url and not 'material_niedostepny' in stream_url):
							settings_setProxy(t._args[1])
							break
						else:
							stream_url=''
					if stream_url or dialog.iscanceled():
						break
				dialog.close()
	
	if isinstance(stream_url,list):
		label= [x.get('title') for x in stream_url]
		bitrate = [x.get('bitrate') for x in stream_url]
		if len(label)>1:
			s =getQuality(label,bitrate)
			stream_url = stream_url[s].get('url') if s>-1 else ''
		else:
			stream_url = stream_url[0].get('url')
	if stream_url:
		if 'Manifest.ism' in stream_url:
			mo,lk=stream_url.split('|')
			mo=vod.getRealStream(mo)
			kukz=my_addon.getSetting('kukhead')
		#	xbmc.executebuiltin('Notification(Strumień DASH, ' + 'KODI 18 - materiał z DRM' + ', 1200)')
			listitem = xbmcgui.ListItem(path=mo)
			listitem.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
			listitem.setProperty('inputstream.adaptive.license_key', lk+kukz)#B{SSM}
			listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
			listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
			listitem.setMimeType('application/dash+xml')
			listitem.setContentLookup(False)			
		else:
			listitem = xbmcgui.ListItem(path=stream_url)
		xbmcplugin.setResolvedUrl(addon_handle, True, listitem)
	else:
		xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem(path=''))
	
elif mode[0]=='vodTVP_przegapiles':
	an = my_addon.getSetting('antenaV')
	wa = my_addon.getSetting('antenaN') if an else 'Wszystkie anteny'
	da = my_addon.getSetting('dataV')
	ta = my_addon.getSetting('dataN') if da else 'Wszystkie daty'
	(episodes, data) = vod.vodTVP_przegapiles(an, da, ta)
	data_lab = []
	data_val = []
	
	if len(data):
		for d in data:
			data_lab.append(d.get('label'))
			data_val.append(d.get('data'))
	
	my_addon.setSetting('data_lab',str(data_lab))
	my_addon.setSetting('data_val',str(data_val))
	
	addLinkItem("[COLOR lightblue]Wybierz antenę:[/COLOR] [B]"+wa+"[/B]",'' , mode='filtr:antena', iconimage='', IsPlayable=False)
	addLinkItem("[COLOR lightblue]Wybierz datę:[/COLOR] [B]"+ta+"[/B]", '', mode='filtr:data', iconimage='', IsPlayable=False)
	
	if len(episodes):
		for e in episodes:
			addLinkItem(e.get('title',''), e.get('id',''), 'vodTVP_play', infoLabels=e, iconimage=e.get('img',None), fanart=e.get('fanart',None))
	xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
	xbmcplugin.endOfDirectory(addon_handle)
elif 'filtr' in mode[0]:
	sf = mode[0].split(":")[-1]
	
	if sf == 'antena':
		label = vod.ant_lab
		value = vod.ant_val
		msg = 'Wybierz antenę:'
	elif sf == 'data':
		label = eval(my_addon.getSetting('data_lab'))
		value = eval(my_addon.getSetting('data_val'))
		msg = 'Wybierz datę:'
	else:
		label = ''
	
	if label and value:
		s = xbmcgui.Dialog().select(msg, label)
		s = s if s > -1 else 0
		my_addon.setSetting(sf+'V',value[s])
		my_addon.setSetting(sf+'N',label[s])
		xbmc.executebuiltin('XBMC.Container.Refresh')
	xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
	xbmcplugin.endOfDirectory(addon_handle)
elif mode[0]=='vodTVP':
	(katalog,episodes) = vod.vodTVPapi(ex_link,page)
	for e in episodes:
		addLinkItem(e.get('title',''), e.get('filename',''), 'vodTVP_play',
					infoLabels=e,iconimage=e.get('img',None),fanart=e.get('fanart',None))
	for one in katalog:
		addDir(one['title'],ex_link=one['id'],page=one.get('page',1),mode='vodTVP',iconImage=one.get('img'))
	xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
	xbmcplugin.endOfDirectory(addon_handle)
elif mode[0] == 'folder':
	if fname == 'TVP info Live':
		out = get_tvpLiveStreams(ex_link)
		for one in out:
			addLinkItem(one['title'], one['url'], 'palyLiveVideo', iconimage=one['img'])
	elif fname == '[COLOR blue]vod.TVP.pl[/COLOR]':
		lo = vod.vodTVP_root()
		for k in lo:
			addDir(k.get('title','').title().encode('utf-8'),str(k.get('id','')),mode='vodTVP')
	elif fname == 'Regionalne':
		lo = vod.getRegional()
		for k in lo:
			addDir(k.get('title','').title().encode('utf-8'),str(k.get('id','')),mode='vodTVP')
	else:
		scanTVPsource(ex_link)
	xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)
	xbmcplugin.endOfDirectory(addon_handle)
