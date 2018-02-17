# -*- coding: utf-8 -*-
import routing
import logging
import xbmcaddon
from resources.lib import kodiutils, kodilogging
import xbmc
from xbmcgui import ListItem, Dialog
from xbmcplugin import addDirectoryItem, endOfDirectory, getSetting, setContent
import requests

ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()
dialog = Dialog()
lbryurl = getSetting(plugin.handle, 'lbryurl')
nsfw = getSetting(plugin.handle, 'nsfw')=='true'

@plugin.route('/')
def index():
    #addDirectoryItem(plugin.handle, plugin.url_for(
    #    speech_menu), ListItem("Connect via spee.ch web portal"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(
        connect_to_daemon), ListItem("Connect via local lbrynet daemon"), True)
    endOfDirectory(plugin.handle)

@plugin.route('/lbry/connect')
def connect_to_daemon():
    try:
        result = requests.post(lbryurl, json={"method":"status"})
        result.raise_for_status()
        #addDirectoryItem(plugin.handle, plugin.url_for(lbry_search), ListItem("Search"), True)
        addDirectoryItem(plugin.handle, plugin.url_for(show_videos), ListItem('Show Videos'), True)
        endOfDirectory(plugin.handle)
    except:
        dialog.ok('Error', ('Could not connect to the lbrynet daemon. Make sure'
            ' that the daemon is running and that the address is configured.'))
        endOfDirectory(plugin.handle, False)

@plugin.route('/lbry/videos')
def show_videos():
    result = requests.post(lbryurl, json={'method':'file_list'})
    result = result.json()['result']
    setContent(plugin.handle, 'movies')

    for r in result:
        if r['mime_type'].startswith('video'):
            url = r['download_path']

            if r['metadata']:
                s = r['metadata']['stream']['metadata']
                if nsfw or not s['nsfw']:
                    li = ListItem(s['title'])
                    if s['thumbnail']:
                        li.setArt({'thumb':s['thumbnail'],
                            'poster':s['thumbnail'],
                            'fanart':s['thumbnail']})
                    if s['description']:
                        li.setInfo('video', {'plot':s['description']})
                    if s['author']:
                        li.setInfo('video', {'writer':s['author']})
                    elif 'channel_name' in r:
                        li.setInfo('video', {'writer':r['channel_name']})

            else:
                li = ListItem(r['file_name'])
            li.setMimeType(r['mime_type'])

            addDirectoryItem(plugin.handle, url, li)
    endOfDirectory(plugin.handle)

@plugin.route('/imagedisplay/<image>')
def image_display(image):
    pass

@plugin.route('/lbry/search')
def lbry_search():
    query = dialog.input('Search Lbry')
    result = requests.post(lbryurl, json={'method':'resolve', 'params':{'uri': query }})
    for r in result:
        pass
    endOfDirectory(plugin.handle)

@plugin.route('/speech')
def speech_menu():
    addDirectoryItem(plugin.handle, plugin.url_for(speech_search), ListItem('Search'))
    endOfDirectory(plugin.handle)

@plugin.route('/speech/search')
def speech_search():
    query = dialog.input('search on spee.ch')

def run():
    plugin.run()
