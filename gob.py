#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright © 2013 Zulip, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

ZULIP_STREAMS = ['social', 'engineering']
# Easily make a bot from your settings page: https://zulip.com/#settings
ZULIP_BOT_NAME = 'Giphy' # We recommend making this 'Giphy' or 'Gob'
ZULIP_USER     = 'giphy-bot@example.com'
ZULIP_API_KEY  = 'a1b2c3d4e5f601234567890123456789'

GIPHY_API_KEY  = 'dc6zaTOxFJmzC'
#-----------------------------------------------------

import zulip
import random
import requests
import traceback
requests_json_is_function = callable(requests.Response.json)

CLIENT = None
VERSION = '0.1'

def get_client():
    return CLIENT

def reply(msg):
    def _reply(content):
        if msg['type'] == 'stream':
            CLIENT.send_message(dict(
                type='stream',
                to=msg['display_recipient'],
                subject=msg['subject'],
                content=content
            ))
        else:
            CLIENT.send_message(dict(
                type='private',
                to=msg['sender_email'],
                content=content
            ))
    return _reply


class GiphyPlugin:
    def get_random_giphy_url(self, search_term):
        try:
            params = {'q': search_term, 'api_key': GIPHY_API_KEY}
            r = requests.get('http://api.giphy.com/v1/gifs/search', params=params)
            if requests_json_is_function:
                json_result = r.json()
            else:
                json_result = r.json
            gifs = json_result.get('data', None)
            if not gifs:
                return None

            desired_gif_data = random.choice(gifs)
            return desired_gif_data['images']['original']['url']
        except:
            traceback.print_exc()

    def get_search_term(self, msg):
        allowable_names = ['/giphy',
                           '@**%s**' % (ZULIP_BOT_NAME,),
                           '@%s' % (ZULIP_BOT_NAME,),]
        for name in allowable_names:
            name += ' '
            if msg['content'].lower().startswith(name.lower()):
                return msg['content'][len(name):]
        return None

    def process_message(self, reply, msg):
        if msg['type'] == 'private' and msg['sender_email'] != ZULIP_USER:
            search_term = msg['content']
        else:
            search_term = self.get_search_term(msg)
        if not search_term:
            return
        desired_gif_url = self.get_random_giphy_url(search_term)
        if desired_gif_url:
            content = '[](%s)' % desired_gif_url
        else:
            content = 'No results. But where did the lighter fluid come from?'
        reply(content)

PLUGINS = [GiphyPlugin()]

def run():
    global CLIENT
    CLIENT = zulip.Client(email=ZULIP_USER,
                          api_key=ZULIP_API_KEY,
                          client='Giphy bot v%s' % VERSION)
    CLIENT.add_subscriptions([{"name": stream_name} for stream_name in ZULIP_STREAMS])

    def process_plugin_message(plugin, message):
        if hasattr(plugin, 'process_message'):
            plugin.process_message(
                reply(message),
                message)

    def process_message(message):
        for plugin in PLUGINS:
            try:
                process_plugin_message(plugin, message)
            except Exception as e:
                print e

    CLIENT.call_on_each_message(process_message)

if __name__ == "__main__":
    run()