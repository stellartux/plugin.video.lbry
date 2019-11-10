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
        print('Lbry RPC error', result.json()['error']['code'], result.json()['error']['message'])
'''

import routing
import logging
import xbmcaddon
from resources.lib import kodiutils, kodilogging
import xbmc
from xbmcgui import ListItem, Dialog, NOTIFICATION_ERROR, INPUT_NUMERIC
from xbmcplugin import addDirectoryItem, addDirectoryItems, endOfDirectory, getSetting, setContent
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
    except Exception as e:
        dialog.notification(translate(30110), result.json()['error']['message'], NOTIFICATION_ERROR)
        xbmc.log(str(e))
        endOfDirectory(ph, False)

@plugin.route('/')
def index():
    #addDirectoryItem(ph, plugin.url_for(lbry_menu), ListItem(translate(30101)), True)
    #addDirectoryItem(ph, plugin.url_for(speech_menu), ListItem(translate(30100)), True)
    #endOfDirectory(ph)
    lbry_menu()

@plugin.route('/lbry/menu')
def lbry_menu():
    addDirectoryItem(ph, plugin.url_for(lbry_search), ListItem(translate(30102)), True)
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
    dialog.ok(translate(30119), translate(30120) + str(balance['total']) + translate(30121),
        translate(30145) + str(balance['available']) + translate(30121),
        translate(30146) + str(balance['reserved']) + translate(30121))

@plugin.route('/lbry/wallet/unused_address')
def show_unused_address():
    address = lbry_rpc('address_unused')
    dialog.ok(translate(30122), address)

@plugin.route('/lbry/file_delete/<file_name>')
def file_delete(file_name):
    if dialog.yesno(translate(30115),translate(30116)):
        if (lbry_rpc('file_delete', {'file_name': file_name, 'delete_from_download_dir': True})):
            dialog.notification(translate(30130), translate(30132))
            xbmc.executebuiltin('Container.Refresh')
        else:
            dialog.notification(translate(30110), '', NOTIFICATION_ERROR)

@plugin.route('/lbry/videos')
def show_videos():
    result = lbry_rpc('file_list')
    setContent(ph, 'movies')
    items = []
    for r in result:
        if r['mime_type'].startswith('video'):
            if 'metadata' in r:
                if (not nsfw and ('nsfw' in r['metadata']) and r['metadata']['nsfw']):
                    continue
                li = make_video_listitem(r, r['metadata'])
            else:
                li = ListItem(r['file_name'])
            li.setMimeType(r['mime_type'])
            if r['download_path'] != None:
                url = r['download_path']
                #li.addContextMenuItems([(translate(30112), 'RunPlugin(' + plugin.url_for(file_delete, file_name=r['file_name']) + ')')])
            else:
                url = r['streaming_url']
            li.addContextMenuItems([(translate(30125) + ' ' + (r['channel_name'] or translate(30133)), 'RunPlugin(' + plugin.url_for(send_tip, claim_id=r['claim_id'], channel_name=(r['channel_name'] or translate(30133))) + ')')])
            items.append((url, li))
    addDirectoryItems(ph, items, len(items))
    endOfDirectory(ph)

def make_video_listitem(item, metadata):
    li = ListItem(metadata['title'] if 'title' in metadata else item['file_name'] if 'file_name' in item else '')
    if 'thumbnail' in metadata and 'url' in metadata['thumbnail']:
        li.setArt({'thumb':metadata['thumbnail']['url'],
            'poster':metadata['thumbnail']['url'],
            'fanart':metadata['thumbnail']['url']})
    if 'description' in metadata:
        li.setInfo('video', {'plot':s['description']})
    if 'author' in metadata:
        li.setInfo('video', {'writer':metadata['author']})
    elif 'channel_name' in item:
        li.setInfo('video', {'writer':item['channel_name']})
    return li

'''Show search input query box'''
@plugin.route('/lbry/search')
def lbry_search():
    query = dialog.input(translate(30106))
    search_page(query, 1)

'''Show paginated search results'''
@plugin.route('/lbry/search/<query>/<page>')
def search_page(query, page):
    page = int(page)
    if query != "":
        result = lbry_rpc('claim_search', {'name': query, 'page': page, 'page_size': int(getSetting(ph, 'page_size'))})
        items = []
        for item in result['items']:
            if item['value_type'] == 'stream':
                url = plugin.url_for(get_file, uri=r['permanent_url'][7:])
                li = make_video_listitem(item, item['value'])
                items.append((url, li))
        addDirectoryItems(ph, items, result['page_size'])
        if (result['total_pages'] > 1):
            addDirectoryItem(ph, plugin.url_for(lbry_menu), ListItem(translate(30144)), True)
            if (page > 1):
                addDirectoryItem(ph, plugin.url_for(search_page, query=query, page=page-1), ListItem(translate(30140)), True)
            if (page < result['total_pages']):
                addDirectoryItem(ph, plugin.url_for(search_page, query=query, page=page+1), ListItem(translate(30141)), True)
        endOfDirectory(ph)
    else:
        endOfDirectory(ph, False)

'''Download file associated with URI'''
@plugin.route('/lbry/get/<uri>')
def get_file(uri):
    stuff = lbry_rpc('get', {'uri': uri, 'save_file': True})
    xmbc.log(stuff)

'''Get the UI string associated with an id in the user's language'''
def translate(id):
    return ADDON.getLocalizedString(id)

@plugin.route('/speech')
def speech_menu():
    addDirectoryItem(ph, plugin.url_for(speech_search), ListItem(translate(30102)))
    endOfDirectory(ph)

@plugin.route('/speech/search')
def speech_search():
    query = dialog.input(translate(30109))

'''Send a tip to the owner of a claim id'''
@plugin.route('/lbry/send_tip/<claim_id>/<channel_name>')
def send_tip(claim_id, channel_name=translate(30133)):
    amount = dialog.input(translate(30127))
    try:
        amount = float(amount)
    except:
        dialog.notification(translate(30110), translate(30131), NOTIFICATION_ERROR)
        return
    if (dialog.yesno(translate(30124), translate(30128) + str(amount) + translate(30129) + channel_name + '?')):
        lbry_rpc('support_create', {'claim_id': claim_id, 'amount': str(amount), 'tip': True})

'''Starts the plugin routing system'''
def run():
    plugin.run()
