# -*- coding: utf-8 -*-
# Module: default
# Author: ostvanc
# Created on: 16.02.2020
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

# Imported libraries

from bs4 import BeautifulSoup
from cloudscraper import CloudScraper
import requests

import js2py
#import pyperclip
import re
import sys

from urllib import urlencode, quote_plus
from urlparse import parse_qsl

import xbmcgui
import xbmcplugin


# Global variables

BASE_URL = 'https://4anime.to'
RANDOM_URL = BASE_URL + '/random'
GENRE_URL = BASE_URL + '/genre'
LOGO_URL = BASE_URL + '/static/logo.png'


def get_url(kwargs):
    # Füge die Cloudflare credentials hinzu
    kwargs.update(_credentials)
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def get_html_document(url):
    headers = {'user-agent': _credentials['user-agent']}
    cookies = {'cf_clearance' : _credentials['cf_clearance'], '__cfduid' : _credentials['__cfduid']}
    r = requests.get(url, headers=headers, cookies=cookies)
    document = r.text
    return document


def retrieve_credentials():
    user_agent = _params.get('user-agent')
    cf_clearance = _params.get('cf_clearance')
    cf_duid = _params.get('__cfduid')
    check = user_agent and cf_clearance and cf_duid
    if check:
        return {'user-agent' : user_agent, 'cf_clearance' : cf_clearance, '__cfduid' : cf_duid}
    else:
        scraper = CloudScraper(interpreter='nodejs', recaptcha={'native': 'return_response'})
        credentials, user_agent = scraper.get_tokens(BASE_URL)
        credentials['user-agent'] = user_agent
        return credentials

def create_list_item(label, info, art, is_playable):
    list_item = xbmcgui.ListItem(label=label)
    list_item.setInfo('video', info)
    list_item.setArt(art)
    if is_playable:
        list_item.setProperty('IsPlayable', 'true')
    return list_item


def list_genre(page_url):
    html_document = get_html_document(page_url)
    soup = BeautifulSoup(html_document, 'html.parser')
    
    genre = soup.find_all('a', {'id' : 'titleleft'})[1].text
    
    a_prev = soup.find('a', {'class' : 'previouspostslink'})
    if a_prev:
        label = '<< Previous Page <<'
        info = {}
        art = {}
        is_playable = False
        list_item = create_list_item(label, info, art, is_playable)
        is_folder = not(is_playable)
        params = {'action' : 'genre', 'url' : a_prev['href']}
        url = get_url(params)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    
    a_next = soup.find('a', {'class' : 'nextpostslink'})
    if a_next:
        label = '>> Next Page >>'
        info = {}
        art = {}
        is_playable = False
        list_item = create_list_item(label, info, art, is_playable)
        is_folder = not(is_playable)
        params = {'action' : 'genre', 'url' : a_next['href']}
        url = get_url(params)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    
    genrestuff = soup.find('div', {'id' : 'genrestuff'})
    divs = genrestuff.find_all('div', {'id' : 'headerDIV_4'})
    for div in divs:
        anchors = div.find_all('a')
        a = anchors[0]
        img = a.img['src']
        href = a['href']
        label = anchors[1].text
        year = anchors[2].text
        info = {'year' : year}
        art = {'icon' : img, 'thumb' : img, 'poster' : img, 'banner' : img, 'fanart' : img}
        is_playable = False
        list_item = create_list_item(label, info, art, is_playable)
        is_folder = not(is_playable)
        params = {'action' : 'list', 'url' : href}
        url = get_url(params)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    
    xbmcplugin.setPluginCategory(_handle, genre)
    xbmcplugin.setContent(_handle, 'videos')    
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)
    
    
def list_genres():
    xbmcplugin.setPluginCategory(_handle, 'Genres')
    xbmcplugin.setContent(_handle, 'videos')
    
    html_document = get_html_document(GENRE_URL)
    soup = BeautifulSoup(html_document, 'html.parser')
    
    #Get the title of this tv show
    lis = soup.find_all('li', {'class' : 'sf-level-0'})
    for li in lis:
        genre = li.input['value']
        label = li.label.text
        info = {}
        art = {}
        is_playable = False
        list_item = create_list_item(label, info, art, is_playable)
        is_folder = not(is_playable)
        page_url = '{0}/{1}'.format(GENRE_URL, genre)
        params = {'action' : 'genre', 'url' : page_url}
        url = get_url(params)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)



def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, 'Categories')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'tvshows')
    
    label = 'Genre'
    info = {}
    art = {}
    is_playable = False
    list_item = create_list_item(label, info, art, is_playable)
    is_folder = not(is_playable)
    params = {'action' : 'genre'}
    url = get_url(params)
    xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    
    label = 'Random'
    info = {}
    art = {}
    is_playable = False
    list_item = create_list_item(label, info, art, is_playable)
    is_folder = not(is_playable)
    params = {'action' : 'list', 'url' : RANDOM_URL}
    url = get_url(params)
    xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    
    label = 'Search'
    info = {}
    art = {}
    is_playable = False
    list_item = create_list_item(label, info, art, is_playable)
    is_folder = not(is_playable)
    params = {'action' : 'search'}
    url = get_url(params)
    xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def list_episodes(url):
    """
    Create the list of video categories in the Kodi interface.
    """
    html_document = get_html_document(url)
    soup = BeautifulSoup(html_document, 'html.parser')
    
    #Get the title of this tv show
    div = soup.find('p', {'class' : 'single-anime-desktop'})
    
    tvshowtitle = div.text
    
    #Get the cover image of this tv show
    div = soup.find('div', {'class' : 'cover'})
    image_url = div.img['src']
    
    #Get the genre of this tv show
    div = soup.find('div', {'class' : 'ui tag horizontal list'})
    items = div.find_all('a', {'class' : 'item'})
    genre = []
    for it in items:
        g = it.text
        genre.append(g)
    
    #Get the description of this tv show
    div = soup.find('div', {'id' : 'description-mob'})
    p = div.find_all('p')
    description = p[1].text
    
    #First find the div with the proper tab_id
    ul = soup.find('ul', {'class' : 'episodes range active'})
    #Then get the corresponding ancestor
    lis = ul.find_all('li', {})
    
    info = {'genre' : genre, 
            'plot' : description,
            'tvshowtitle' : tvshowtitle,
            'mediatype' : 'episode'
            }
    art = {'icon' : image_url}
    
    for li in lis:
        a = li.a
        href = a['href']
        title = a.text
    
        #Create the ListItem
        is_playable = True
        
        list_item = create_list_item(title, info, art, is_playable)
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        content_url = href
        params = {'action' : 'play', 'url' : content_url}
        url = get_url(params)
        is_folder = not(is_playable)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    

    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, tvshowtitle)
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'tvshows')    
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)   

def mock_document(code):
    return 'var output = ""; document = {write: function(text){output += text;}}' + code + '; output'
    
def play_video(url):
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=url)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item) 

def play_episode(content_url):
    #All websites with content contain the div with the video play class
    html_document = get_html_document(content_url)
    soup = BeautifulSoup(html_document, 'html.parser')
    
    #Get the JavaScript to be evaluated
    scripts = soup.find_all('script', {'type' : 'text/javascript'})
    for s in scripts:
        code = s.text
        if 'eval' in code:
            code = mock_document(code)
            try:
                output = js2py.eval_js(code)
                soup = BeautifulSoup(output, 'html.parser')
                #Get the HTML 5 video tag
                video = soup.find('video')
                if video:
                    video_url = video['src']        
                    play_video(video_url)
                    return
                a = soup.find('a')
                #Alternatively we will scrape the anchor
                if a:
                    href = a['href']
                    play_video(href)
                    return                    
            except Exception as e:
                xbmc.log(str(e), xbmc.LOGWARNING)

                
def resolve_search():
    query = xbmcgui.Dialog().input('Search')
    if query:
        url = BASE_URL + '/?s=' + quote_plus(query)
        html_document = get_html_document(url)
        soup = BeautifulSoup(html_document, 'html.parser')
        container = soup.find('div', {'class' : 'container'})
        items = container.find_all('div', {'id' : 'headerDIV_95'})
        for it in items:
            a = it.a
            content_url = a['href']
            image_url = a.img['src']
            title = a.div.text
            
            info = {}
            art = {'icon' : image_url}
            is_playable = False
            
            list_item = create_list_item(title, info, art, False)
            # Create a URL for a plugin recursive call.
            # Example: plugin://plugin.video.example/?action=listing&category=Animals
            params = {'action' : 'list', 'url' : content_url}
            url = get_url(params)
            is_folder = not(is_playable)
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        
        # Add a sort method for the virtual folder items (alphabetically, ignore articles)
        xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(_handle)


def resolve():
    # Check the parameters passed to the plugin
    # There are basically two possible actions in Kodi: list and play
    action = _params.get('action')
    url = _params.get('url')
    if action:
        if action == 'list':
            list_episodes(url)
        elif action == 'play':
            play_episode(url)
        elif action == 'search':
            resolve_search()
        elif action == 'genre':
            if url:
                list_genre(url)
            else:
                list_genres()
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(str(_params)))
    else:
        # If the plugin is called from Kodi UI without any other parameters,
        # display the list of video categories
        list_categories()
        

#############################
# Entry point of the script #
#############################

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

# Parse a URL-encoded paramstring to the dictionary of
# {<parameter>: <value>} elements
_params = dict(parse_qsl(sys.argv[2][1:]))

# Retrieve Cloudflare credentials
_credentials = retrieve_credentials()


if __name__ == '__main__':
    # Call the resolve function
    resolve()
