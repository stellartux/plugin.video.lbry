# -*- coding: utf-8 -*-

import routing
import logging
import xbmcaddon
from resources.lib import kodiutils
from resources.lib import kodilogging
from xbmcgui import ListItem, Dialog
from xbmcplugin import addDirectoryItem, endOfDirectory
import requests

ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()
dialog = Dialog()

@plugin.route('/')
def index():
    addDirectoryItem(plugin.handle, plugin.url_for(
        speech_menu), ListItem("Connect via web portal"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(
        connect_to_daemon), ListItem("Connect via local daemon"), True)
    endOfDirectory(plugin.handle)

@plugin.route('/lbry/connect')
def connect_to_daemon():
    try:
        result = requests.post('http://localhost:5279', json={"method":"settings_get"})
        result.raise_for_status()
    except:
        dialog.ok('Error', ('Could not connect to the lbrynet daemon. Make sure'
            ' that the daemon is running and that the address is configured.'))

@plugin.route('/speech')
def speech_menu():
    addDirectoryItem(plugin.handle, plugin.url_for(speech_search), ListItem("Search"))
    endOfDirectory(plugin.handle)

@plugin.route('/speech/search')
def speech_search():
    query = dialog.input('search on spee.ch')

@plugin.route('/lbry/localfiles')
def show_localfiles():
    result = requests.post('http://localhost:5279', json={"method"})
    # get the local lbry directory
    # create an entry (thumbnail?) for each file
    endOfDirectory(plugin.handle)

def run():
    plugin.run()
