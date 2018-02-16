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
lbryurl = 'http://localhost:5279'

@plugin.route('/')
def index():
    addDirectoryItem(plugin.handle, plugin.url_for(
        speech_menu), ListItem("Connect via spee.ch web portal"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(
        connect_to_daemon), ListItem("Connect via local lbrynet daemon"), True)
    endOfDirectory(plugin.handle)

@plugin.route('/lbry/connect')
def connect_to_daemon():
    try:
        result = requests.post('http://localhost:5279', json={"method":"settings_get"})
        result.raise_for_status()
        addDirectoryItem(plugin.handle, plugin.url_for(lbry_search), ListItem("Search"), True)
    except:
        dialog.ok('Error', ('Could not connect to the lbrynet daemon. Make sure'
            ' that the daemon is running and that the address is configured.'))

    addDirectoryItem(plugin.handle, plugin.url_for(show_local_files), ListItem('Show local files'), True)
    endOfDirectory(plugin.handle)

@plugin.route('/lbry/localfiles')
def show_local_files():
    result = requests.post(lbryurl, json={'method':'file_list'})
    result = result.json()['result']
    for r in result:
        if r['metadata']:
            li = ListItem(r['metadata']['stream']['metadata']['title'])
            if r['metadata']['stream']['metadata']['thumbnail']:
                li.setArt({'thumb':r['metadata']['stream']['metadata']['thumbnail']})
            addDirectoryItem(plugin.handle, plugin.url_for(open_file, r['download_path']), li)
    endOfDirectory(plugin.handle)

@plugin.route('lbry/localfiles/play/<file>')
def open_file():
    pass

@plugin.route('/lbry/search')
def lbry_search():
    query = dialog.input('Search Lbry')
    result = requests.post(lbryurl, json={'{}'.format(query)})

@plugin.route('/speech')
def speech_menu():
    addDirectoryItem(plugin.handle, plugin.url_for(speech_search), ListItem('Search'))
    endOfDirectory(plugin.handle)

@plugin.route('/speech/search')
def speech_search():
    query = dialog.input('search on spee.ch')

def run():
    plugin.run()
