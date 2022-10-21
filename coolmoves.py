from __future__ import unicode_literals

import os
import sys
import youtube_dl
from gphotospy import authorize
from gphotospy.media import Media
from gphotospy.album import Album

TMP_FN = 'out.mp4'
ALBUM_NAME = 'Cool Moves'
CLIENT_SECRET_FILE = "credentials.json"

def time_to_sec(t):
	tms = reversed([int(x) for x in t.split(':')])
	sec = 0
	for i, t in enumerate(tms):
		sec += t * (60 ** i)

	return sec

def find_format(formats, fid):
	for x in formats:
		if x['format_id'] == fid:
			return x

def upload(file, desc):
	service = authorize.init(CLIENT_SECRET_FILE)

	album_manager = Album(service)
	media_manager = Media(service)

	album_id = None
	for album in album_manager.list():
		if album.get('title') == ALBUM_NAME:
			album_id = album.get('id')
			break

	if album_id is None:
		album_id = album_manager.create(ALBUM_NAME).get('id')

	media_manager.stage_media(file, desc)
	media_manager.batchCreate(album_id)

def main():
	if len(sys.argv) < 4 or len(sys.argv) > 5:
		print(f'usage: {sys.argv[0]} link start end [description]')
		return

	link = sys.argv[1]
	start = time_to_sec(sys.argv[2])
	end = time_to_sec(sys.argv[3])
	desc = sys.argv[4] if len(sys.argv) == 5 else ''

	start = max(0, start - 1) # to compensate for cutoff at the start by ffmpeg
	duration = end - start

	ydl_opts = {}
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		result = ydl.extract_info(link, download=False)
		url = find_format(result['formats'], '22')['url']

		os.system(f'ffmpeg -y -ss {start} -i \'{url}\' -t {duration} -c:v copy -c:a copy {TMP_FN}')

	# upload out.mp4 to album named Cool Moves
	upload(TMP_FN, desc)

if __name__ == '__main__':
	main()
