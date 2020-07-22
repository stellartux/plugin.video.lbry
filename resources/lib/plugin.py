# -*- coding: utf-8 -*-
'''
paste this into Python interpreter to do lbry rpc calls easily

from requests import post
def lbry_rpc(method, params={}):
    try:
        result = post('http://localhost:5279', json={'method': method, 'params': params})
        result.raise_for_status()
        return result.json()['result']
    except Exception as e:
        print('Lbry RPC error', str(e), result.json()['error']['message'])
'''

import routing
import logging
import xbmcaddon
from resources.lib import kodiutils, kodilogging
import xbmc
from xbmcgui import ListItem, Dialog, NOTIFICATION_ERROR, INPUT_NUMERIC
from xbmcplugin import addDirectoryItem, addDirectoryItems, endOfDirectory, setContent
from requests import post

ADDON = xbmcaddon.Addon()
translate = ADDON.getLocalizedString
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()
ph = plugin.handle
dialog = Dialog()

def lbry_rpc(method, params={}):
    try:
        rpc_url = ADDON.getSetting('lbryurl')
        if rpc_url == '':
            raise Exception('No URL for RPC.')
        result = post(rpc_url, json={'method': method, 'params': params})
        result.raise_for_status()
        return result.json()['result']
    except Exception as e:
        dialog.notification(translate(30110), str(e), NOTIFICATION_ERROR)
        xbmc.log(str(e))
        endOfDirectory(ph, False)

@plugin.route('/')
def lbry_menu():
    addDirectoryItem(ph, plugin.url_for(lbry_search), ListItem(translate(30102)), True)
    addDirectoryItem(ph, plugin.url_for(show_videos, page=1), ListItem(translate(30103)), True)
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

@plugin.route('/lbry/file_delete/<path:file_name>')
def file_delete(file_name):
    if dialog.yesno(translate(30115),translate(30116)):
        if lbry_rpc('file_delete', {'file_name': file_name, 'delete_from_download_dir': True}):
            dialog.notification(translate(30130), translate(30132))
            xbmc.executebuiltin('Container.Refresh')
        else:
            dialog.notification(translate(30110), translate(30111), NOTIFICATION_ERROR)

@plugin.route('/lbry/videos/<page>')
def show_videos(page):
    page = int(page)
    result = lbry_rpc('file_list', {'page': page, 'page_size': int(ADDON.getSetting('page_size'))})
    # { total_items, items, page, total_pages, page_size }
    setContent(ph, 'movies')
    items = []
    nsfw = ADDON.getSettingBool('nsfw')
    for r in result['items']:
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
            else:
                url = r['streaming_url']

            context_items = [
                    (   # Send tip context menu
                        translate(30125) + ' ' + (r['channel_name'] or translate(30133)),
                        'RunPlugin(' + plugin.url_for(send_tip, claim_id=r['claim_id'], channel_name=(r['channel_name'] or translate(30133))) + ')'
                    ),
                    (   # File delete context menu
                        translate(30112),
                        'RunPlugin(' + plugin.url_for(file_delete, file_name=r['file_name']) + ')'
                    )
                ]
            li.addContextMenuItems(context_items)
            items.append((url, li))

    description = translate(30142).format(result['page'], result['total_pages'])
    if result['total_pages'] > 1 and page > 1:
        li = ListItem(translate(30140))
        li.setInfo('video', {'plot': description})
        li.setIsFolder(True)
        items.append((plugin.url_for(show_videos, page = page - 1), li))
    if page < result['total_pages']:
        li = ListItem(translate(30141))
        li.setInfo('video', {'plot': description})
        li.setIsFolder(True)
        items.append((plugin.url_for(show_videos, page = page + 1), li))

    addDirectoryItems(ph, items, len(items))
    endOfDirectory(ph)

def make_video_listitem(item, metadata):
    li = ListItem(metadata['title'] if 'title' in metadata else item['file_name'] if 'file_name' in item else '')
    if 'thumbnail' in metadata and 'url' in metadata['thumbnail']:
        li.setArt({'thumb':metadata['thumbnail']['url'],
            'poster':metadata['thumbnail']['url'],
            'fanart':metadata['thumbnail']['url']})
    if 'description' in metadata:
        li.setInfo('video', {'plot':metadata['description']})
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
    if query != '':
        result = lbry_rpc('claim_search', {'name': query, 'page': page, 'page_size': int(ADDON.getSetting('page_size')), 'stream_types':['video']})
        items = []
        for item in result['items']:
            if item['value_type'] == 'stream':
                url = plugin.url_for(get_file, name=item['normalized_name'], id=item['claim_id'])
                li = make_video_listitem(item, item['value'])
                items.append((url, li))
        addDirectoryItems(ph, items, result['page_size'])
        total_pages = int(result['total_pages'])
        if (total_pages > 1):
            addDirectoryItem(ph, plugin.url_for(lbry_menu), ListItem(translate(30144)), True)
            if (page > 1):
                addDirectoryItem(ph, plugin.url_for(search_page, query=query, page=page-1), ListItem(translate(30140)), True)
            if (page < total_pages):
                addDirectoryItem(ph, plugin.url_for(search_page, query=query, page=page+1), ListItem(translate(30141)), True)
        endOfDirectory(ph)
    else:
        endOfDirectory(ph, False)

'''Download file associated with name and id'''
@plugin.route('/lbry/get/<name>/<id>')
def get_file(name, id):
    uri = name + '#' + id
    claim_info = lbry_rpc('resolve', {'urls': uri})
    if 'error' in claim_info[uri]:
        dialog.notification(translate(30110), claim_info[uri]['error'], NOTIFICATION_ERROR)
        return
    elif 'fee' in claim_info[uri]['value']:
        if not dialog.yesno(translate(30147), translate(30148).format(str(claim_info[uri]['value']['fee']['amount']), str(claim_info[uri]['value']['fee']['currency']))):
            return
    result = lbry_rpc('get', {'uri': uri, 'save_file': True})
    xbmc.Player().play(result['streaming_url'])

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
