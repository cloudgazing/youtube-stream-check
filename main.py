import argparse
import json
import re
import sys
import urllib.request

url = ''
page = ''
data = {}
stream = {
    'status': 'offline',
    'id': None,
    'title': None,
    'description': None,
    'thumbnail': None,
}

def valid_url(value, arg):
    global url

    if arg == 'handle':
        url = f'https://www.youtube.com/{value}/streams' if value.startswith('@') else f'https://www.youtube.com/@{value}/streams'
    if arg == 'id':
        url = f'https://www.youtube.com/channel/{value}/streams'
    if arg == 'url':
        m = re.search(r'(m.)?(youtube\.com/(\w+/)?@?\w+)/*', value)
        url = f'https://www.{m.group(2)}/streams' if m else ''

    try:
        request = urllib.request.Request(url)
        response = urllib.request.urlopen(request)
    except:
        sys.tracebacklimit = 0
        raise Exception(f'Invalid {arg}')

    return url

def ping():
    global url
    global page
    global data

    header = {'Accept-Language': 'en-US'}
    request = urllib.request.Request(url, headers=header)
    response = urllib.request.urlopen(request)
    page = str(response.read().decode())

    pattern = r'<script nonce="[-\w]+">var ytInitialData = (.*);</script>'
    j = re.search(pattern, page)

    data = json.loads(j.group(1)) if j else sys.exit('!!JSON LOADS ERROR!!')

    if '{"text":" waiting"}' in page:
        stream['status'] = 'waiting'
    elif '{"text":" watching"}' in page:
        stream['status'] = 'watching'
    else: 
        stream['status'] = 'offline'

def stream_update():
    global data
    global stream

    if stream['title'] != data['contents']['twoColumnBrowseResultsRenderer']['tabs'][3]['tabRenderer']['content']['richGridRenderer']['contents'][0]['richItemRenderer']['content']['videoRenderer']['title']['runs'][0]['text']:
        stream['title'] = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][3]['tabRenderer']['content']['richGridRenderer']['contents'][0]['richItemRenderer']['content']['videoRenderer']['title']['runs'][0]['text']
        print(f'Stream title has been changed to "{stream["title"]}"')
    if stream['description'] != data['contents']['twoColumnBrowseResultsRenderer']['tabs'][3]['tabRenderer']['content']['richGridRenderer']['contents'][0]['richItemRenderer']['content']['videoRenderer']['descriptionSnippet']['runs'][0]['text']:
        stream['description'] = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][3]['tabRenderer']['content']['richGridRenderer']['contents'][0]['richItemRenderer']['content']['videoRenderer']['descriptionSnippet']['runs'][0]['text']
        print(f'Stream description has been changed to "{stream["description"]}"')
    if stream['thumbnail'] != data['contents']['twoColumnBrowseResultsRenderer']['tabs'][3]['tabRenderer']['content']['richGridRenderer']['contents'][0]['richItemRenderer']['content']['videoRenderer']['thumbnail']['thumbnails'][3]['url']:
        stream['thumbnail'] = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][3]['tabRenderer']['content']['richGridRenderer']['contents'][0]['richItemRenderer']['content']['videoRenderer']['thumbnail']['thumbnails'][3]['url']
        print(f'Stream thumbnail has been changed to "{stream["thumbnail"]}"')


def main():
    global url
    global page
    global data
    global stream

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-handle', default=None, help='YouTube channel handle (has an "@" at the beggining)')
    group.add_argument('-id', default=None, help='YouTube channel ID (not the channel handle!!)')
    group.add_argument('-url', default=None, help='The YouTube channel URL')
    arg = parser.parse_args()

    if arg.handle:
        url = valid_url(arg.handle, 'handle')
    if arg.id:
        url = valid_url(arg.id, 'id')
    if arg.url:
        url = valid_url(arg.url, 'url')

    ping()

    while stream['status']:
        if stream['status'] == 'offline':
            print(
            'Stream offline.\n'
            'Will ping continuously and update when it schedules...'
            )
        while stream['status'] == 'offline':
            ping()

        stream['id'] = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][3]['tabRenderer']['content']['richGridRenderer']['contents'][0]['richItemRenderer']['content']['videoRenderer']['videoId']
        stream['title'] = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][3]['tabRenderer']['content']['richGridRenderer']['contents'][0]['richItemRenderer']['content']['videoRenderer']['title']['runs'][0]['text']
        stream['description'] = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][3]['tabRenderer']['content']['richGridRenderer']['contents'][0]['richItemRenderer']['content']['videoRenderer']['descriptionSnippet']['runs'][0]['text']
        stream['thumbnail'] = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][3]['tabRenderer']['content']['richGridRenderer']['contents'][0]['richItemRenderer']['content']['videoRenderer']['thumbnail']['thumbnails'][3]['url']

        if stream['status'] == 'waiting':
            print(
            f'Stream scheduled! | youtu.be/{stream["id"]}\n'
            f'Stream title: "{stream["title"]}")\n'
            'Will ping continuously and update when something changes and when it goes live...'
            )
        while stream['status'] == 'waiting':
            stream_update()
            ping()

        if stream['status'] == 'watching':
            print(
            f'Stream is now LIVE! | youtu.be/{stream["id"]}\n'
            f'Stream title: "{stream["title"]}")\n'
            'Will ping continuously and update when something changes and when it goes offline...'
            )
        while stream['status'] == 'watching':
            stream_update()
            ping()

        if stream['status'] == 'offline':
            print(
            'Stream ended.\n'
            '-------------'
            )
        for key in stream:
            if key != 'status':
                stream[key] = None

if __name__ == '__main__':
    main()