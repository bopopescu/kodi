# -*- coding: utf-8 -*-
"""
The channel model UI module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
Licensed under MIT License
"""

# pylint: disable=import-error
import xbmcgui
import xbmcplugin

import resources.lib.mvutils as mvutils

from resources.lib.channel import Channel


class ChannelUI(Channel):
    """
    The channel model view class

    Args:
        plugin(MediathekView): the plugin object

        sortmethods(array, optional): an array of sort methods
            for the directory representation. Default is
            `[ xbmcplugin.SORT_METHOD_TITLE ]`

        nextdir(str, optional):
    """

    def __init__(self, plugin, sortmethods=None, nextdir='initial'):
        super(ChannelUI, self).__init__()
        self.plugin = plugin
        self.handle = plugin.addon_handle
        self.nextdir = nextdir
        self.sortmethods = sortmethods if sortmethods is not None else [
            xbmcplugin.SORT_METHOD_TITLE]
        self.count = 0

    def begin(self):
        """
        Begin a directory containing channels
        """
        for method in self.sortmethods:
            xbmcplugin.addSortMethod(self.handle, method)

    def add(self, altname=None):
        """
        Add the current entry to the directory

        Args:
            altname(str, optional): alternative name for the entry
        """
        resultingname = self.channel if self.count == 0 else '%s (%d)' % (
            self.channel, self.count, )
        list_item = xbmcgui.ListItem(
            label=resultingname if altname is None else altname)
        icon = 'special://home/addons/' + self.plugin.addon_id + \
            '/resources/icons/' + self.channel.lower() + '-m.png'
        list_item.setArt({
            'thumb': icon,
            'icon': icon
        })
        xbmcplugin.addDirectoryItem(
            handle=self.handle,
            url=mvutils.build_url({
                'mode': self.nextdir,
                'channel': self.channelid
            }),
            listitem=list_item,
            isFolder=True
        )

    def end(self):
        """ Finish a directory containing channels """
        xbmcplugin.endOfDirectory(self.handle)
