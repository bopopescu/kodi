# -*- coding: utf-8 -*-
import sys
import os
from urlparse import parse_qsl
import urllib
import requests
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
params = dict(parse_qsl(sys.argv[2][1:]))
addon = xbmcaddon.Addon(id='plugin.video.pilot.wp')

login_url = 'https://pilot.wp.pl/api/v1/user_auth/login'
main_url = 'https://pilot.wp.pl/api/v1/channels/list?device=androidtv'
video_url = 'https://pilot.wp.pl/api/v1/channel/'
close_stream_url = 'https://pilot.wp.pl/api/v1/channels/close'

headers = {
    'user-agent': 'ExoMedia 4.3.0 (43000) / Android 8.0.0 / foster_e',
    'accept': 'application/json',
    'x-version': 'pl.videostar|3.25.0|Android|26|foster_e',
    'content-type': 'application/json; charset=UTF-8'
}

username = addon.getSetting('username')
password = addon.getSetting('password')
file_name = addon.getSetting('fname')
path = addon.getSetting('path')
sessionid = params.get('sessionid', '')

addonInfo = xbmcaddon.Addon().getAddonInfo
dataPath = xbmc.translatePath(addonInfo('profile')).decode('utf-8')
cacheFile = os.path.join(dataPath, 'cache.db')


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


def add_item(name, image, is_folder, is_playble, payload, plot=''):
    list_item = xbmcgui.ListItem(label=name)

    if is_playble:
        list_item.setProperty("IsPlayable", 'true')
    else:
        list_item.setProperty("IsPlayable", 'false')

    list_item.setInfo(type='video', infoLabels={
                      'title': name, 'sorttitle': name, 'plot': plot})
    list_item.setArt({'thumb': image, 'poster': image, 'banner': image})
    xbmcplugin.addDirectoryItem(
        handle=addon_handle,
        url=build_url(payload),
        listitem=list_item,
        isFolder=is_folder
    )


def saveToDB(table_name, value):
    import sqlite3
    import os
    if os.path.exists(cacheFile):
        os.remove(cacheFile)
    else:
        print('File does not exists')
    conn = sqlite3.connect(cacheFile, detect_types=sqlite3.PARSE_DECLTYPES,
                           cached_statements=20000)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS Cache(%s TEXT)' % table_name)
    c.execute("INSERT INTO Cache('%s') VALUES ('%s')" % (table_name, value))
    conn.commit()
    c.close()


def readFromDB():
    import sqlite3
    conn = sqlite3.connect(cacheFile, detect_types=sqlite3.PARSE_DECLTYPES,
                           cached_statements=20000)
    c = conn.cursor()
    c.execute("SELECT * FROM Cache")
    for row in c:
        if row:
            c.close()
            return row[0]


def cookiesToString(cookies):
    try:
        return "; ".join([str(x) + "=" + str(y) for x, y in cookies.get_dict().items()])
    except Exception as e:
        print (e)
        return ''


def login():
    if len(password) > 0 and len(username) > 0:
        data = {'device': 'AndroidTV', 'login': username, 'password': password}

        response = requests.post(
            login_url,
            json=data,
            verify=False,
            headers=headers
        )

        meta = response.json().get('_meta', None)
        if meta is not None:
            if meta.get('error', {}).get('name', None) is not None:
                xbmcgui.Dialog().notification('Nieudane logowanie', 'Sprawdź login i hasło w ustawieniach wtyczki.',
                                              xbmcgui.NOTIFICATION_ERROR, 5000)
                return ''

        saveToDB('wppilot_cache', cookiesToString(response.cookies))
        return cookiesToString(response.cookies)

    else:
        xbmcgui.Dialog().notification('Nieudane logowanie', 'Sprawdź login i hasło w ustawieniach wtyczki.',
                                      xbmcgui.NOTIFICATION_ERROR, 5000)
        return ''


def stream_url(video_id, retry=False):
    cookies = readFromDB()
    if not sessionid or len(video_id) == 0:
        return ''

    url = video_url + video_id
    data = {'format_id': '2', 'device_type': 'android'}

    headers.update({'Cookie': cookies})
    response = requests.get(
        url,
        params=data,
        verify=False,
        headers=headers,
    ).json()

    meta = response.get('_meta', None)
    if meta is not None:
        token = meta.get('error', {}).get('info', {}).get('stream_token', None)
        if token is not None:
            json = {'channelId': video_id, 't': token}
            response = requests.post(
                close_stream_url,
                json=json,
                verify=False,
                headers=headers
            ).json()
            if response.get('data', {}).get('status', '') == 'ok' and not retry:
                return stream_url(video_id, True)
            else:
                return

    if 'hls@live:abr' in response[u'data'][u'stream_channel'][u'streams'][0][u'type']:
        return response[u'data'][u'stream_channel'][u'streams'][0][u'url'][0]
    else:
        return response[u'data'][u'stream_channel'][u'streams'][1][u'url'][0]


def play(id):
    manifest = stream_url(id)

    if len(manifest) == 0:
        return
    manifest = manifest + '|user-agent=' + headers['user-agent']
    play_item = xbmcgui.ListItem(path=manifest)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


def channels():
    if not sessionid:
        return []
    cookies = readFromDB()
    headers.update({'Cookie': cookies})
    response = requests.get(
        main_url,
        verify=False,
        headers=headers,
    ).json()

    return response.get('data', [])


def home():
    if not sessionid:
        return

    for item in channels():
        if item.get('access_status', '') != 'unsubscribed':
            title = item.get('name', '')
            icon = item.get('thumbnail_mobile', '')
            id = item.get('id', None)
            add_item(title, icon, False, True, {
                     'mode': 'play', 'id': id, 'sessionid': sessionid})

    xbmcplugin.endOfDirectory(addon_handle)


def generate_m3u():
    if not sessionid:
        return

    if file_name == '' or path == '':
        xbmcgui.Dialog().notification('WP Pilot', 'Ustaw nazwe pliku oraz katalog docelowy.',
                                      xbmcgui.NOTIFICATION_ERROR)
        return

    xbmcgui.Dialog().notification('WP Pilot', 'Generuje liste M3U.',
                                  xbmcgui.NOTIFICATION_INFO)
    data = '#EXTM3U\n'

    for item in channels():
        if item.get('access_status', '') != 'unsubscribed':
            id = item.get('id', None)
            title = item.get('name', '')
            data += '#EXTINF:-1,%s\nplugin://plugin.video.pilot.wp?action=PLAY&channel=%s\n' % (
                title, id)

    f = xbmcvfs.File(path + file_name, 'w')
    f.write(data.encode('utf-8'))
    f.close()

    xbmcgui.Dialog().notification('WP Pilot', 'Wygenerowano liste M3U.',
                                  xbmcgui.NOTIFICATION_INFO)


def route():
    global sessionid
    if not sessionid:
        sessionid = login()

    mode = params.get('mode', None)
    action = params.get('action', '')

    if action == 'BUILD_M3U':
        generate_m3u()
    elif action == 'PLAY':
        id = params.get('channel', '')
        play(id)
    else:
        if not mode:
            home()
        elif mode == 'play':
            id = params.get('id', '')
            play(id)


if __name__ == '__main__':
    route()
