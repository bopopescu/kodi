# -*- coding: utf-8 -*-
# Module: default
# Author: Philip Janicki
# Created on: 21.11.2019
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

# Imported libraries

import sys

from urllib import urlencode
import urllib2
from urlparse import parse_qsl

from bs4 import BeautifulSoup

import xbmcgui
import xbmcplugin

# Global variables

BASE_URL = 'https://telewizjarepublika.pl'

TVR_LOGO_URL = 'https://static.wirtualnemedia.pl/media/top/telewizja-republika-2019.jpg'
CONTENT_URL = BASE_URL + '/wideo'

LIVESTREAM_URL = 'http://redir.cache.orange.pl/jupiter/o1-cl7//live/tvrepublika/live.m3u8'

YOUTUBE_URL_PLAYLIST_PREFIX = 'https://www.youtube.com/playlist?list='

YOUTUBE_PLUGIN_URL_PREFIX = 'plugin://plugin.video.youtube/'
# Wichtig: Der / am Ende ist essentiell!
YOUTUBE_PLUGIN_URL_PLAYLIST_FORMAT = YOUTUBE_PLUGIN_URL_PREFIX + 'playlist/{}/'

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def get_html_document(url):
    response = urllib2.urlopen(url)
    document = response.read()
    return document

def create_list_item(title, image_url, is_playable):
    list_item = xbmcgui.ListItem(label=title)
    list_item.setInfo('video', {'title': title,
                                'genre': title})
    list_item.setArt({'thumb': image_url, 'icon' : image_url, 'fanart': image_url})
    
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
        
    LIST_ITEMS = [
        {'title' : 'Na żywo', 'image_url' : TVR_LOGO_URL, 'action' : 'play'},
        {'title' : 'Mediateka', 'image_url' : TVR_LOGO_URL, 'action' : 'list'}    
    ]
    
    for li in LIST_ITEMS:
        is_playable = (li['action'] == 'play')
        list_item = create_list_item(li['title'], li['image_url'], is_playable)
        is_folder = not(is_playable)
        url = get_url(action=li['action'])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


PLAYLIST_DICT = {
	'PL_2LK9doeytZuoJZYB1wWF15Mi2dQQI5e' : 'Koniec Systemu',
	'PL_2LK9doeytbdTNFcpsLFQp7itv_oUIYg' : 'Kulisy Manipulacji',
	'PL_2LK9doeytaaYocH77AnGIbAnbfLDGgj' : 'Otwartym Textem',
	'PL_2LK9doeytZOuJAWRYyHhHUg_pCbUDca' : 'Polityczna Kawa',
	'PL_2LK9doeytbNsRJqdzWi4Ph26-m4NwnY' : 'Salonik Polityczny'
}

def get_playlist_title(playlist_id):
    return PLAYLIST_DICT.get(playlist_id, playlist_id)


def list_magazines():
    
    #xbmcgui.Dialog().ok("Debug", image_url)
    
    """
    Create list of TV shows on this channel.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, 'Programy')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    
    list = [
        {'title' : 'Poland Daily Live', 
            'image_url' : 'https://polanddaily.com/images/polanddaily.png',
            'playlist_id' : 'UUtgTrj49wi_GrB3t1d9U8Fw'},
        {'title' : 'Magazyn Wojskowy', 
            'image_url' : BASE_URL + '/images/landingpage/mw.png', 
            'playlist_id' : 'PL_2LK9doeytaIG87Y6KSvm7n_wpWQ7sw7'},
        {'title' : 'Zawód Żołnierz', 
            'image_url' : BASE_URL + '/images/landingpage/zawodzolnierz.png', 
            'playlist_id' : 'PL_2LK9doeytZUOuzn3J55t_Ss9goin_7x'},
        {'title' : 'Telewizja Republika', 
            'image_url' : TVR_LOGO_URL, 
            'playlist_id' : 'UUc282c_TN8xIba_Z6GaDnQw'}
    ]

    #Extend the list with the dynamic items:
    
    html_document = get_html_document(CONTENT_URL)
    soup = BeautifulSoup(html_document, 'html.parser')
    magazines = soup.find_all('div', {'class' : 'magazyn-item'})
    
    for mi in magazines:
        # We want the reference url and the image url
        a = mi.a
        href = a['href']
        src = a.img['src']
        
        playlist_id = href.replace(YOUTUBE_URL_PLAYLIST_PREFIX,'')
        image_url = BASE_URL + src
        title = get_playlist_title(playlist_id)
        
        elem = {'title' : title, 'playlist_id' : playlist_id, 'image_url' : image_url}
        list.append(elem)
    
    #Now 
    
    for elem in list:
        
        title = elem['title']
        playlist_id = elem['playlist_id']
        url = YOUTUBE_PLUGIN_URL_PLAYLIST_FORMAT.format(playlist_id)
        
        # Create a list item with a text label and a thumbnail image.
        image_url = elem['image_url']
        list_item = create_list_item(title, image_url, False) 
        
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def play_video(url):
    xbmc.log('Incoming video URL: ' + url, xbmc.LOGNOTICE)
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=url)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
        

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
        if params['action'] == 'list':
            list_magazines()
        elif params['action'] == 'play':
            # Show the list of programs
            play_video(LIVESTREAM_URL)
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