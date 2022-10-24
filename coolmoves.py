from __future__ import unicode_literals

import os
import sys
import youtube_dl
from gphotospy import authorize
from gphotospy.media import Media
from gphotospy.album import Album

TMP_FN = 'tmpout'
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

def readtime(ln):
	s, e = ln.split()[1:]
	s = max(0, time_to_sec(s) - 1)
	e = time_to_sec(e)
	return (s, e - s)

def readfile(fn):
	with open(fn) as f:
		lns = [ln.strip() for ln in f]

		link = lns[0]
		univ_desc = []
		times = []
		descs = []

		desc = []
		for ln in lns[1:]:
			if ln.startswith('--'):
				if len(times) == 0:
					univ_desc = '\n'.join(desc)
				else:
					descs.append('\n'.join(desc))

				times.append(readtime(ln))
				desc = []
			else:
				desc.append(ln)

		descs.append('\n'.join(desc))

		descs = [f'{univ_desc}\n{desc}' for desc in descs]

		return link, times, descs

def download(link, times, fn):
	start, duration = times

	ydl_opts = {}
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		result = ydl.extract_info(link, download=False)
		url = find_format(result['formats'], '22')['url']

		os.system(f'ffmpeg -y -ss {start} -i \'{url}\' -t {duration} -c:v copy -c:a copy {fn}')

def upload(files, descs):
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

	for fn, d in zip(files, descs):
		media_manager.stage_media(fn, d)

	print('uploading cool moves')
	media_manager.batchCreate(album_id)

def main():
	if len(sys.argv) != 2:
		print(f'usage: {sys.argv[0]} <inputfile>')
		return

	link, times, descs = readfile(sys.argv[1])
	fns = [f'{TMP_FN}_{i}.mp4' for i in range(len(times))]

	for t, d, fn in zip(times, descs, fns):
		download(link, t, fn)

	upload(fns, descs)

	for fn in fns:
		os.remove(fn)

if __name__ == '__main__':
	main()
