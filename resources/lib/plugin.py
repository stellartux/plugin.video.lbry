# -*- coding: utf-8 -*-
'''
paste this into Python interpreter to do lbry rpc calls easily

import requests
def lbry_rpc(method, params={}):
    try:
        result = requests.post('http://localhost:5279', json={'method': method, 'params': params})
        result.raise_for_status()
        return result.json()['result']
    except:
        print('Lbry RPC error')
'''

import routing
import logging
import xbmcaddon
from resources.lib import kodiutils, kodilogging
import xbmc
from xbmcgui import ListItem, Dialog, NOTIFICATION_ERROR, INPUT_NUMERIC
from xbmcplugin import addDirectoryItem, endOfDirectory, getSetting, setContent
import requests

ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()
ph = plugin.handle
dialog = Dialog()
nsfw = getSetting(ph, 'nsfw')=='true'

def lbry_rpc(method, params={}):
    try:
        result = requests.post(getSetting(ph, 'lbryurl'), json={'method': method, 'params': params})
        result.raise_for_status()
        return result.json()['result']
    except:
        dialog.notification(translate(30107), translate(30108), NOTIFICATION_ERROR)
        endOfDirectory(ph, False)

@plugin.route('/')
def index():
    addDirectoryItem(ph, plugin.url_for(lbry_menu), ListItem(translate(30101)), True)
    #addDirectoryItem(ph, plugin.url_for(speech_menu), ListItem(translate(30100)), True)
    endOfDirectory(ph)

@plugin.route('/lbry/menu')
def lbry_menu():
    #addDirectoryItem(ph, plugin.url_for(lbry_search), ListItem(translate(30102)), True)
    addDirectoryItem(ph, plugin.url_for(show_videos), ListItem(translate(30103)), True)
    #addDirectoryItem(ph, plugin.url_for(show_images), ListItem(translate(30104)), True)
    #addDirectoryItem(ph, plugin.url_for(show_web), ListItem(translate(30105)), True)
    addDirectoryItem(ph, plugin.url_for(wallet_menu), ListItem(translate(30117)), True)
    endOfDirectory(ph)

@plugin.route('/lbry/wallet')
def wallet_menu():
    addDirectoryItem(ph, plugin.url_for(show_balance), ListItem(translate(30118)), True)
    addDirectoryItem(ph, plugin.url_for(show_unused_address), ListItem(translate(30123)), True)
    endOfDirectory(ph)

@plugin.route('/lbry/wallet/balance')
def show_balance():
    balance = lbry_rpc('account_balance')
    dialog.ok(translate(30119), translate(30120) + str(balance) + translate(30121))

@plugin.route('/lbry/wallet/unused_address')
def show_unused_address():
    address = lbry_rpc('address_unused')
    dialog.ok(translate(30122), address)

@plugin.route('/lbry/file_delete/<file_name>')
def file_delete(file_name):
    if dialog.yesno(translate(30115),translate(30116)):
        result = lbry_rpc('file_delete', {'file_name': file_name, 'delete_target_file': True})
        xbmc.executebuiltin("Container.Refresh")
        #if result:
        #    myClaims = lbry_rpc('claim_list')
        #    for c in myClaims:
        #        if c['claim_id'] == claim_id:
        #            value = lbry_rpc('claim_search', {'claim_id': claim_id})
        #            if dialog.yesno(translate(30113), translate(30114)):
        #                lbry_rpc('stream_abandon', {'claim_id': claim_id})
        #    xbmc.executebuiltin("Container.Refresh")
        #else:
        #    dialog.notification(translate(30110), translate(30111), image=NOTIFICATION_ERROR)

@plugin.route('/lbry/videos')
def show_videos():
    result = lbry_rpc('file_list')
    setContent(ph, 'movies')
    for r in result:
        if r['mime_type'].startswith('video'):
            url = r['download_path']
            if r['metadata']:
                s = r['metadata']
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
            #li.addContextMenuItems([(translate(30112), 'RunPlugin(' + plugin.url_for(file_delete, {'file_name': r['file_name']}) + ')')])
            #li.addContextMenuItems([(translate(30125) + ' ' + r['channel_name'], 'RunPlugin(' + plugin.url_for(send_tip, claim_id=r['claim_id'], channel_name=r['channel_name']) + ')')])
            addDirectoryItem(ph, url, li)
    endOfDirectory(ph)

@plugin.route('/lbry/images')
def show_images():
    result = lbry_rpc('file_list')
    setContent(ph, 'images')

    for r in result:
        if r['mime_type'].startswith('image'):
            url = r['download_path']

            if r['metadata']:
                s = r['metadata']
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

            addDirectoryItem(ph, url, li)
    endOfDirectory(ph)

@plugin.route('/lbry/search')
def lbry_search():
    query = dialog.input(translate(30106))
    if query != "":
        result = lbry_rpc('resolve', {'uri': query})
        for r in result:
            pass
        endOfDirectory(ph)
    else:
        endOfDirectory(ph, False)

def translate(id):
    return ADDON.getLocalizedString(id)

@plugin.route('/speech')
def speech_menu():
    addDirectoryItem(ph, plugin.url_for(speech_search), ListItem(translate(30102)))
    endOfDirectory(ph)

@plugin.route('/speech/search')
def speech_search():
    query = dialog.input(translate(30109))

@plugin.route('/lbry/send_tip/<claim_id>/<channel_name>')
def send_tip(claim_id, channel_name):
    amount = dialog.input(translate(30127))
    try:
        amount = float(amount)
    except:
        dialog.notification(translate(30130), translate(30131), NOTIFICATION_ERROR)
        return
    if (dialog.yesno(translate(30124), translate(30128) + str(amount) + translate(30129) + channel_name + '?')):
        dialog('DO THE THING', 'This is where I would send the tip, if the API were done.')

def run():
    plugin.run()
