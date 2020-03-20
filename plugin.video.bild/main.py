# -*- coding: utf-8 -*-
# Module: default
# Author: ostvanc
# Created on: 21.11.2019
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

# Imported libraries

from json import JSONDecoder

import json
import re
import sys

from urllib import urlencode, quote_plus
from urllib2 import Request, urlopen
from urlparse import parse_qsl

from bs4 import BeautifulSoup, Comment

import xbmcgui
import xbmcplugin


# Global variables

BASE_URL = 'https://www.bild.de'
ENTRY_URL = BASE_URL + '/video'
LOGO_URL = 'https://bilder.bild.de/fotos/bild-logo-35166394/Bild/43.bild.png'

FANART_URL = 'https://media.diepresse.com/images/q45/uploads_1120/e/1/f/1408543/bild-zeitung_1369233061139760.jpg'


CONTEXT_ID_PATTERN = '\[(\d+)\/(\d+)\/(\d+)\]'
REQUEST_URL_FORMAT = 'https://www.bild.de/navi/-{0},contentContextId={1},view=dropdown.bild.html'


JSON_PATTERN_STRING = '\{.*\}'
UNICHAR_PATTERN_STRING = '&#(\d+);'


def reformat_unichars(input):
    """
    Bereinigt einen eingegebenen String von Darstellungsfehler von bestimmten Unicode-Zeichen (Umlaute, Aprostrophe, Anführungszeichen, ...).
    """
    output = input
    pattern = re.compile(UNICHAR_PATTERN_STRING, re.DOTALL)
    match = pattern.search(output)
    while match:
        chunk = match.group(0)
        number = int(match.group(1))
        pretty_char = unichr(number)
        output = output.replace(chunk, pretty_char)
        match = pattern.search(output)
    output = output.replace('&amp;', '&')
    output = output.replace('&quot;', '"')
    output = output.replace('&apos;', "'")
    return output
    

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def get_json_data(url):
    document = get_html_document(url)
    data = json.loads(document)
    return data

def get_html_document(url):
    request = Request(url, headers={'User-Agent' : 'Mozilla/5.0'})
    response = urlopen(request)
    document = response.read()
    return document

def create_list_item(label, info, art, is_playable):
    list_item = xbmcgui.ListItem(label=label)
    list_item.setInfo('video', info)
    list_item.setArt(art)
    if is_playable:
        list_item.setProperty('IsPlayable', 'true')
    return list_item


def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, 'Categories')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')    
    
    html_document = get_html_document(BASE_URL)
    soup = BeautifulSoup(html_document, 'html.parser')
    livestream = soup.find('div', {'class' : 'cms-video-02'})
    if livestream:
        div = livestream.div
        json_url = BASE_URL + div['data-media']
        json_data = get_json_data(json_url)
        
        label = 'Livestream'
        title = reformat_unichars(json_data['title'])
        description = reformat_unichars(json_data['description'])
        info = {'title' : title, 'plot' : description}
        art = {'poster' : json_data['poster'], 'fanart' : FANART_URL}
        video_url = json_data['clipList'][0]['srces'][0]['src']
        is_playable = True
        list_item = create_list_item(label, info, art, is_playable)
        is_folder = not(is_playable)
        url = get_url(action='play', url=video_url)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    
    html_document = get_html_document(ENTRY_URL)
    soup = BeautifulSoup(html_document, 'html.parser')
    
    #Zuerst brauchen wir die Context-ID, diese steht im allerersten Kommentar
    comment = soup.find(string=lambda text: isinstance(text, Comment))
    pattern = re.compile(CONTEXT_ID_PATTERN)
    match = pattern.search(comment)
    context_id = match.group(1)
    
    
    nav_bars = soup.find('ul', {'class' : 'nav-ressorts clearfix'})
    data_drop_cid = None
    
    for li in nav_bars.find_all('li'):
        if li.has_attr('data-drop-cid'):
            a = li.a
            if a.text == 'Video':
                data_drop_cid = li.get('data-drop-cid')
                break
                
    request_url = REQUEST_URL_FORMAT.format(data_drop_cid, context_id)
    html_document = get_html_document(request_url)
    soup = BeautifulSoup(html_document, 'html.parser')
    
    #Danach erzeugen wir eine Liste mit li-Items aus drei verschiedenen Quellen
    li_list = []
    
    content = soup.find('div', {'class' : 'content s3'})
    for li in content.find_all('li'):
        li_list.append(li)
    
    # Jetzt ist die Liste mit den lis fertig und wir können loslegen
    for li in li_list:
        a = li.find('a')
        title = a.text
        content_url = BASE_URL + a['href']
        
        info = {'plot' : title}
        art = {'poster' : LOGO_URL, 'fanart' : FANART_URL}
        is_playable = False
        
        list_item = create_list_item(title, info, art, is_playable)
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='list', url=content_url)
        is_folder = not(is_playable)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    
    #xbmcgui.Dialog().ok("Debug", image_url)
    
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    #xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def list_videos(url):
    #xbmcgui.Dialog().ok("Debug", url)
    
    """
    Create the list of video categories in the Kodi interface.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, 'Videos')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    
    html_document = get_html_document(url)
    soup = BeautifulSoup(html_document, 'html.parser')
    
    # Die Bild-Videos befinden sich als JSON-Objekte im JavaScript-Code der Seite
    scripts = soup.find_all('script')
    for script in scripts:
        js_code = script.text
        if "videoJSON" in js_code:
            pattern = re.compile(JSON_PATTERN_STRING, re.DOTALL)
            match = pattern.search(js_code)
            if match:
                data = match.group()
                json_data = None
                try:
                    json_data = json.loads(data)
                except:
                    pass
                if json_data:
                    
                    #xbmcgui.Dialog().ok("Debug", str(json_data))
                    #break
                    
                    # Bild-Plus-Videos können nicht ohne Credentials abgespielt werden, daher werden sie nicht angezeigt.
                    premium = json_data['premium'] 
                    if not(premium):
                    
                        headline = json_data['headline']
                        title = reformat_unichars(json_data['title'])
                        description = reformat_unichars(json_data['description'])
                        durationSec = json_data['durationSec']
                        poster = json_data['poster']
                        clipList = json_data['clipList']
                        
                        source = clipList[0]['srces'][0]['src']
                        
                        #Create the ListItem
                        info = {'title' : title, 'mediatype' : 'video', 'plot' : description, 'duration' : durationSec}
                        art = {'poster' : poster, 'fanart' : poster}
                        is_playable = True
                        
                        list_item = create_list_item(title, info, art, is_playable)
                        # Create a URL for a plugin recursive call.
                        # Example: plugin://plugin.video.example/?action=listing&category=Animals
                        content_url = source
                        url = get_url(action='play', url=content_url)
                        is_folder = not(is_playable)
                        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)      
                
        
        
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)
    
def play_video(url):
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=url)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
    
# def resolve_search(params):
    # query = xbmcgui.Dialog().input('Search')
    # if query:
        # url = BASE_URL + '/?s=' + quote_plus(query)
        # html_document = get_html_document(url)
        # soup = BeautifulSoup(html_document, 'html.parser')
        # container = soup.find('div', {'class' : 'container'})
        # items = container.find_all('div', {'id' : 'headerDIV_95'})
        # for it in items:
            # a = it.a
            # content_url = a['href']
            # image_url = a.img['src']
            # title = a.div.text
            
            # info = {}
            # art = {'icon' : image_url}
            # is_playable = False
            
            # list_item = create_list_item(title, info, art, False)
            # # Create a URL for a plugin recursive call.
            # # Example: plugin://plugin.video.example/?action=listing&category=Animals
            # url = get_url(action='list', url=content_url)
            # is_folder = not(is_playable)
            # xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)        
        
        # # Add a sort method for the virtual folder items (alphabetically, ignore articles)
        # xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        # # Finish creating a virtual folder.
        # xbmcplugin.endOfDirectory(_handle)
    
    
def resolve_list(params):
    url = params['url']
    list_videos(url)
    

def resolve_play(params):
    url = params['url']
    play_video(url)
        

def resolve(paramstring):
    """
    Resolve function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    # There are basically two possible actions in Kodi: list and play
    if params:
        action = params['action']
        if action == 'list':
            resolve_list(params)
        elif action == 'play':
            resolve_play(params)
        elif action == 'search':
            resolve_search(params)
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


#############################
# Entry point of the script #
#############################

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
if __name__ == '__main__':
    # Call the resolve function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    resolve(sys.argv[2][1:])
