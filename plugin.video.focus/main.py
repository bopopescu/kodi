# -*- coding: utf-8 -*-
# Module: default
# Author: ostvanc
# Created on: 12.04.2020
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

# Imported libraries

#from datetime import datetime
#import time

import json
import sys

from urllib import urlencode, quote_plus
from urllib2 import Request, urlopen
from urlparse import parse_qsl

from bs4 import BeautifulSoup, Comment

import xbmcgui
import xbmcplugin


# Global variables

BASE_URL = 'https://www.focus.de'
ENTRY_URL = BASE_URL + '/videos'
LOGO_URL = 'https://images-eu.ssl-images-amazon.com/images/I/51AqBTxRz0L.png'
FANART_URL = 'http://ulutuncok.com/wp-content/uploads/2017/05/focus_bundeswehr-3-von-4.jpg'

FOCUS_DATETIME_FORMAT = '%d.%m.%y, %H:%M'
KODI_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

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
    
    html_document = get_html_document(ENTRY_URL)
    soup = BeautifulSoup(html_document, 'html.parser')
    
    ul = soup.find('ul', {'class' : 'main'})
    items = ul.find_all('a')
    
    for a in items:
        data_id = a.get('data-id')
        if data_id:
            title = a.text
            content_url = a['href']
            info = {'plot' : title}
            art = {'poster' : LOGO_URL, 'fanart' : FANART_URL}
            is_playable = False
        
            list_item = create_list_item(title, info, art, is_playable)
            url = url = get_url(action='list', url=content_url, id=data_id)
            is_folder = not(is_playable)
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    #xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def list_videos(url, data_id):    
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
    
    divs = soup.find_all('div', {'class' : 'vidTeaserSingle'})
    for div in divs:
        a = div.a
        video_url = a['href']
        title = a['title']
        image_url = a.img['data-src']
        
        # Hier ist ein Bug in Python mit dem Datum, mehr unter https://community.smartbear.com/t5/TestComplete-General-Discussions/python-error-in-datetime/td-p/130144
        #date_string = div.span.text
        #date_object = datetime(*(time.strptime(date_string, FOCUS_DATETIME_FORMAT)[0:6]))
        #date_added = date_object.strftime(KODI_DATETIME_FORMAT)
        date_added = None
        
        #Create the ListItem
        info = {'title' : a.span.text, 'mediatype' : 'video', 'plot' : a.h3.text, 'dateadded' : date_added}
        
        art = {'poster' : image_url, 'fanart' : image_url}
        is_playable = True
        
        list_item = create_list_item(title, info, art, is_playable)
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='play', url=video_url)
        is_folder = not(is_playable)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)    
            
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)
    
def play_video(url):
    html_document = get_html_document(url)
    soup = BeautifulSoup(html_document, 'html.parser')
    content_url = None
    script = soup.find_all('script', {'type' : 'application/ld+json'})
    for s in script:
        json_data = json.loads(s.text)
        if 'contentUrl' in json_data:
            content_url = json_data['contentUrl']
            break
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=content_url)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)        
    
    
def resolve_list(params):
    url = params['url']
    data_id = params['id']
    list_videos(url, data_id)
    

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
