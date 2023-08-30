import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta

import pytz


class Stream:
    status = ''
    video_id = ''
    title = ''
    description = ''
    thumbnail = ''
    time_iso = ''
    video_url = ''

    def __init__(self, status, video_id, title, description, thumbnail, time_iso):
        self.status = status
        self.video_id = video_id
        self.title = title
        self.description =description
        self.thumbnail = thumbnail
        self.time_iso = time_iso
        self.video_url = f'https://youtube.com/watch?v={video_id}'

    def __str__(self):
        if self.status == 'scheduled':
            text = (
                f'Stream with ID "{self.video_id}" is scheduled.',
                f'Start time is {self.start()} (California time) - {self.until_start()} from now',
                f'Title: "{self.title}"',
                f'URL: {self.video_url}'
            )
            return '\n'.join(line for line in text)
        if self.status == 'live':
            text = (
                f'Stream with ID "{self.video_id}" is live!',
                f'Title: "{self.title}"',
                f'URL: {self.video_url}'
            )
            return '\n'.join(line for line in text)

    def start(self):
        california_tz = pytz.timezone('America/Los_Angeles')
        datetime_obj = datetime.strptime(self.time_iso, f'%Y-%m-%dT%H:%M:%S%z')
        california_time = datetime_obj.astimezone(california_tz)
        return california_time.strftime(f'%Y-%m-%d %H:%M:%S %Z')

    def until_start(self):
        california_tz = pytz.timezone('America/Los_Angeles')
        datetime_obj = datetime.strptime(self.time_iso, f'%Y-%m-%dT%H:%M:%S%z')
        california_time = datetime_obj.astimezone(california_tz)
        current_time_california = datetime.now(california_tz)
        time_difference = california_time - current_time_california
        hours, minutes, _ = str(time_difference).split(':')
        return f'{hours} hours and {minutes} minutes'

    def same_info(self, other):
        for attr in self.__dict__:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    def update(self, stream):
        print(f'Stream with ID {self.video_id} has been updated\n')
        print(stream)
        return stream

def valid_url(value, arg):
    if arg == 'handle':
        url = f'https://www.youtube.com/{value if value.startswith("@") else f"@{value}"}/streams'
    elif arg == 'id':
        url = f'https://www.youtube.com/channel/{value}/streams'
    elif arg == 'url':
        m = re.search(r'(m.)?(youtube\.com/(\w+/)?@?\w+)/*', value)
        url = f'https://www.{m.group(2)}/streams' if m else ''
    else:
        sys.tracebacklimit = 0
        sys.exit('Invalid argument')

    try:
        request = urllib.request.Request(url)
        _ = urllib.request.urlopen(request)
    except:
        sys.tracebacklimit = 0
        raise Exception(f'Invalid {arg}')

    return url

def site_contents(url):
    header = {'Accept-Language': 'en-US'}
    request = urllib.request.Request(url, headers=header)
    response = urllib.request.urlopen(request)

    return str(response.read().decode())

def get_data(url):
    page = site_contents(url)

    pattern = r'<script nonce="[-\w]+">var ytInitialData = (.*);</script>'
    j = re.search(pattern, page)
    data = json.loads(j.group(1)) if j else sys.exit('!!JSON LOADS ERROR!!')

    return data

def get_ids(data):
    video_ids = []
    index = 0
    def is_stream(data, i):
        try:
            status = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][3]['tabRenderer']['content']['richGridRenderer']['contents'][i]['richItemRenderer']['content']['videoRenderer']['viewCountText']['runs'][1]['text']
            if status == ' watching' or status == ' waiting':
                return True
        except:
            return False
        return True

    while is_stream(data, index):
        video_ids.append(data['contents']['twoColumnBrowseResultsRenderer']['tabs'][3]['tabRenderer']['content']['richGridRenderer']['contents'][index]['richItemRenderer']['content']['videoRenderer']['videoId'])
        index += 1

    return video_ids

def is_stream(video_id):
    url = f'https://www.youtube.com/watch?v={video_id}'
    page = site_contents(url)

    pattern = r'<script nonce="[-\w]+">var ytInitialPlayerResponse = (.*);</script>'
    j = re.search(pattern, page)
    data = json.loads(j.group(1)) if j else sys.exit('!!JSON LOADS ERROR!!')

    try:
        is_live = data['videoDetails']['isLiveContent']
    except:
        return False

    return True if is_live == 'true' else False

def make_stream(video_id):
    url = f'https://youtube.com/watch?v={video_id}'
    page = site_contents(url)

    pattern = r'<script nonce="[-\w]+">var ytInitialPlayerResponse = (.*);</script>'
    j = re.search(pattern, page)
    data = json.loads(j.group(1)) if j else sys.exit('!!JSON LOADS ERROR!!')

    status = 'live' if data['playabilityStatus']['status'] == 'OK' else 'scheduled'
    video_id = data['videoDetails']['videoId']
    title = data['videoDetails']['title']
    description = data['videoDetails']['shortDescription']
    thumbnail = data['videoDetails']['thumbnail']['thumbnails'][4]['url']
    time_iso = None if status == 'live' else data['microformat']['playerMicroformatRenderer']['liveBroadcastDetails']['startTimestamp']

    return Stream(status, video_id, title, description, thumbnail, time_iso)

def video_length(video_id):
    url = f'https://youtube.com/watch?v={video_id}'
    page = site_contents(url)

    pattern = r'<script nonce="[-\w]+">var ytInitialPlayerResponse = (.*);</script>'
    j = re.search(pattern, page)
    data = json.loads(j.group(1)) if j else sys.exit('!!JSON LOADS ERROR!!')

    seconds = data['videoDetails']['lengthSeconds']
    time_obj = timedelta(seconds=seconds)

    return f'{f"{time_obj.days} days " if time_obj.days else ""}{time_obj}'


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-handle', default=None, help='YouTube channel handle (starts with an "@")')
    group.add_argument('-id', default=None, help='YouTube channel ID (not the channel handle!!)')
    group.add_argument('-url', default=None, help='The YouTube channel URL')
    arg = parser.parse_args()

    if arg.handle:
        url = valid_url(arg.handle, 'handle')
    elif arg.id:
        url = valid_url(arg.id, 'id')
    elif arg.url:
        url = valid_url(arg.url, 'url')
    else:
        sys.exit(1)

    data = get_data(url)
    video_ids = get_ids(data)
    streams = [make_stream(video_id) for video_id in video_ids]
    while True:
        if not streams:
            print(f'There are no streams scheduled or live')
        while not streams:
            data = get_data(url)
            video_ids = get_ids(data)
            streams = [make_stream(video_id) for video_id in video_ids]

        for stream in streams:
            print(f'{stream}\n')

        while streams:
            different_ids = list(set(video_ids).symmetric_difference(set(get_ids(data))))
            for video_id in different_ids:
                if is_stream(video_id):
                    if video_id not in video_ids:
                        video_ids.append(video_id)
                        new_stream = make_stream(video_id)
                        streams.append(new_stream)
                        print('New stream!\n')
                        print(f'{new_stream}\n')
                elif video_id in video_ids:
                    print(f'Stream with ID "{video_id}" ended!')
                    print(f'Stream time was {video_length(video_id)}')
                    video_ids.remove(video_id)
                    for stream in streams:
                        if stream.video_id == video_id:
                            if stream.status == 'live':
                                print(f'Stream time was {video_length(video_id)}')
                            streams.remove(stream)

            for index, video_id in enumerate(video_ids):
                stream_diff = make_stream(video_id)
                if not streams[index].same_info(stream_diff):
                    streams[index] = streams[index].update(stream_diff)

            data = get_data(url)

if __name__ == '__main__':
    main()