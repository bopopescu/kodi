# -*- coding: utf-8 -*-
import sys
from urlparse import parse_qsl
import urllib
import requests
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import time
from collections import OrderedDict
from datetime import date, datetime
import pickle
import json
import m3u8
import inputstreamhelper
from HTMLParser import HTMLParser


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
params = dict(parse_qsl(sys.argv[2][1:]))
addon = xbmcaddon.Addon(id='plugin.video.tvpsport')
resources = xbmc.translatePath(addon.getAddonInfo('path') + '/resources/')

headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US',
            'X-Requested-With': 'pl.tvp.tvp_sport',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Linux; U; Android 8.0.0; Nexus 5X Build/OPP3.170518.006) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/39.0.0.0 Safari/537.36 EmbeddedBrowser TVPSportMobileApp'
        }

weekdays = [
    'Poniedziałek',
    'Wtorek',
    'Środa',
    'Czwartek',
    'Piątek',
    'Sobota',
    'Niedziela',
]


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


def build_image_url(image_name):
    url = 'http://s.tvp.pl/images/' + image_name[0] + '/' + image_name[1] + '/' + image_name[2] + '/uid_' + image_name[:-4] + '_width_640_height_360_gs_0' + image_name[-4:]
    print(url)
    return url


def add_item(movie_id, name, description, image, playable):
    s = MLStripper()
    s.feed(description)

    list_item = xbmcgui.ListItem(label=name)
    list_item.setProperty("IsPlayable", playable)
    list_item.setInfo(type='video', infoLabels={
        'title': name,
        'sorttitle': name,
        'plot': s.get_data()
    })
    list_item.setArt({'thumb': image, 'poster': image, 'banner': image, 'fanart': image})
    xbmcplugin.addDirectoryItem(
        handle=addon_handle,
        url=build_url({'mode': 'play', 'id': movie_id}),
        listitem=list_item,
        isFolder=False
    )


def add_folder(name, param={}, fanart=None):
    list_item = xbmcgui.ListItem(name.capitalize())
    if fanart:
        list_item.setArt({'fanart': fanart})
    list_item.setInfo(type='video', infoLabels={
        'title': name,
        'sorttitle': name
    })
    xbmcplugin.addDirectoryItem(
        handle=addon_handle,
        url=build_url(param),
        listitem=list_item,
        isFolder=True
    )


def add_separator(name, image=resources+'transparent.png', param={}):
    list_item = xbmcgui.ListItem(label=name)
    list_item.setProperty("IsPlayable", 'false')
    list_item.setArt({'thumb': image})
    xbmcplugin.addDirectoryItem(
        handle=addon_handle,
        url=build_url(param),
        listitem=list_item,
        isFolder=False
    )


def home():
    add_folder('Dyscypliny', {'mode': 'disciplines'}, resources+'fanart.jpg')
    add_folder('Transmisje', {'mode': 'live'}, resources+'fanart.jpg')
    add_folder('Wideo', {'mode': 'videos'}, resources+'fanart.jpg')
    xbmcplugin.endOfDirectory(addon_handle)


def live():
    streams = requests.get(
        'http://www.api.v3.tvp.pl/shared/listing_blackburst.php?dump=json&nocount=1&type=video&parent_id=3116100&copy=true&direct=true&order=release_date_long,1&count=-1&filter={%22paymethod%22:0}',
        headers=headers,
        verify=False
    ).json()

    sections = {}
    dates = []

    items = streams.get('items', [])
    for item in items:
        if (item.get('release_date_long', 0) + item.get('duration', 0) * 1000) < int(time.time() * 1000.0):
            continue

        release_dt = item.get('release_date_dt')
        if sections.get(release_dt, None):
            sections[release_dt].append(item)
        else:
            sections[release_dt] = []
            sections[release_dt].append(item)

        dates.append(release_dt)

    dates = list(OrderedDict.fromkeys(dates))

    for datestr in dates:

        components = datestr.encode('utf-8', 'ignore').split('-')
        d = date(int(components[0]), int(components[1]), int(components[2]))
        title = weekdays[d.weekday()] + ', ' + components[2] + '-' + components[1] + '-' + components[0]
        now = datetime.now()
        if d.day == now.day and d.month == now.month and d.year == now.year:
            title = 'Dzisiaj'

        add_separator('[I]' + title + '[/I]')
        for item in sections[datestr]:
            movie_id = item.get('asset_id', '')
            release_hour = item.get('release_date_hour', '')
            name = release_hour + ' - ' + item.get('title', '')
            images = item.get('image', [])
            image_dict = next(iter(images), None)
            description = item.get('lead', [])

            image = ''
            if image_dict:
                image = build_image_url(image_dict.get('file_name', None))

            playable = 'false'
            if item.get('play_mode', 0) == 2 and item.get('is_live', False):
                playable = 'true'
                name = '[B]TRWA:[/B] ' + name

            add_item(movie_id, name, description, image, playable)

    xbmcplugin.endOfDirectory(addon_handle)


def videos():
    video_category = params.get('video_category', '432801')
    prev_release_dates = params.get('prev_release_dates', None)

    if prev_release_dates:
        prev_release_dates = pickle.loads(prev_release_dates)
    else:
        prev_release_dates = []

    release_date = None
    if len(prev_release_dates) > 0:
        release_date = prev_release_dates[-1]

    filterstr = '{%27play_mode%27:1,%27playable%27:true}'
    if release_date:
        filterstr = '{%27play_mode%27:1,%20%27release_date_long%27:{%27$lt%27:' + release_date + '}}'

    videos = requests.get(
        'http://www.api.v3.tvp.pl/shared/listing_blackburst.php?dump=json&nocount=1&type=video&parent_id=' + video_category + '&copy=false&direct=false&order=release_date_long,-1&count=15&filter='+filterstr,
        headers=headers,
        verify=False
    ).json()

    def parse_item(item):
        movie_id = item.get('asset_id', '')
        name = item.get('title', '')
        images = item.get('image', [])
        image_dict = next(iter(images), None)
        description = item.get('lead', [])
        image = ''
        if image_dict:
            image = build_image_url(image_dict.get('file_name', None))
        playable = 'true'
        add_item(movie_id, name, description, image, playable)

    if len(prev_release_dates) > 0:
        add_separator(name='<< POPRZEDNIA STRONA', param={'mode': 'prev_page', 'prev_release_dates': pickle.dumps(prev_release_dates), 'video_category': video_category})

    items = videos.get('items', [])
    for item in items:
        parse_item(item)

    release_date_long = str(items[-1].get('release_date_long', None))
    if prev_release_dates:
        prev_release_dates.append(release_date_long)
    else:
        prev_release_dates = [release_date_long]

    if len(items) == 15:
        add_separator(name='NASTĘPNA STRONA >>', param={'mode': 'next_page', 'prev_release_dates': pickle.dumps(prev_release_dates), 'video_category': video_category})

    xbmcplugin.endOfDirectory(addon_handle)


def prev_page():
    video_category = params.get('video_category', '432801')
    prev_release_dates = params.get('prev_release_dates', None)
    if prev_release_dates:
        prev_release_dates = pickle.loads(prev_release_dates)
    else:
        prev_release_dates = []
    prev_release_dates.pop()
    xbmc.executebuiltin('Container.Update("%s",replace)' % build_url({'mode': 'videos', 'prev_release_dates': pickle.dumps(prev_release_dates), 'video_category': video_category}))


def next_page():
    video_category = params.get('video_category', '432801')
    prev_release_dates = params.get('prev_release_dates', None)
    if prev_release_dates:
        prev_release_dates = pickle.loads(prev_release_dates)
    else:
        prev_release_dates = []

    xbmc.executebuiltin('Container.Update("%s",replace)' % build_url({'mode': 'videos', 'prev_release_dates': pickle.dumps(prev_release_dates), 'video_category': video_category}))


def disciplines():
    xbmcplugin.addSortMethod(handle=addon_handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE)

    sub_disciplines = params.get('sub_disciplines', None)

    if sub_disciplines:
        data = pickle.loads(sub_disciplines)
    else:
        with open(resources + '/disciplines.json') as f:
            data = json.load(f)

    for key, value in data.iteritems():
        name = value.get('name', '')
        sub_disciplines = value.get('subcategory', {})

        if sub_disciplines:
            param = {'mode': 'disciplines', 'sub_disciplines': pickle.dumps(sub_disciplines)}
        else:
            param = {'mode': 'videos', 'video_category': key}

        add_folder(name, param, resources+'fanart.jpg')

    xbmcplugin.endOfDirectory(addon_handle)


def play():
    movie_id = params.get('id', None)
    url = 'http://www.tvp.pl/shared/cdn/tokenizer_v2.php?object_id='+movie_id
    content = requests.get(
        url,
        headers=headers,
        verify=False
    ).json()

    stream_url = ''
    for item in content.get('formats', []):
        if item.get('mimeType') == 'application/x-mpegurl':
            stream_url = item.get('url', '')
            break

    playlist = requests.get(
        stream_url,
        headers=headers,
        verify=False
    ).text

    if addon.getSetting('inputstream') == 'false':
        print('str_url false')
        quality = int(addon.getSetting('quality'))
        print(quality)
        if quality > 0:
            variant_m3u8 = m3u8.loads(playlist)
            print(len(variant_m3u8.playlists))
            if variant_m3u8.is_variant and quality <= len(variant_m3u8.playlists):
                stream_url = stream_url.replace('manifest.m3u8', variant_m3u8.playlists[quality-1].uri)
        play_item = xbmcgui.ListItem(path=stream_url)
    else:
        print('str_url true')
        is_helper = inputstreamhelper.Helper('hls')
        if is_helper.check_inputstream():
            play_item = xbmcgui.ListItem(path=stream_url)
            play_item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
            play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
            play_item.setMimeType('application/x-mpegurl')
            play_item.setContentLookup(False)

    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


if __name__ == '__main__':
    mode = params.get('mode', None)

    if not mode:
        home()
    elif mode == 'live':
        live()
    elif mode == 'videos':
        videos()
    elif mode == 'disciplines':
        disciplines()
    elif mode == 'prev_page':
        prev_page()
    elif mode == 'next_page':
        next_page()
    elif mode == 'play':
        play()
