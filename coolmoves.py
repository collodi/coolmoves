from __future__ import unicode_literals

import os
import cv2
import sys
import time
import yt_dlp
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

def get_snippets(lns):
	snippets = []
	seg = []
	for ln in lns:
		if ln.startswith('--'):
			snippets.append(seg)
			seg = []
		else:
			seg.append(ln)

	snippets.append(seg)
	return snippets

def readfile(fn):
	with open(fn) as f:
		lns = [ln.strip() for ln in f]

		times = [readtime(ln) for ln in lns if ln.startswith('--')]

		snippets = get_snippets(lns)

		# get universal description
		univ_desc = '\n'.join(snippets[0])
		snippets = snippets[1:]

		# interpolate link if not exist in snippet
		link = None
		for snip in snippets:
			if snip[0].startswith('http'):
				link = snip[0]
			else:
				snip.insert(0, link)

		links = [snip[0] for snip in snippets]

		# get descriptions
		descs = ['\n'.join(snip[1:]) for snip in snippets]
		if len(univ_desc) > 0:
			descs = [f'{univ_desc}\n{desc}' for desc in descs]

		return links, times, descs

def get_url(link):
	ydl_opts = {}
	with yt_dlp.YoutubeDL(ydl_opts) as ydl:
		result = ydl.extract_info(link, download=False)
		return find_format(result['formats'], '22')['url']

def get_urls(links):
	link_to_url = { link: get_url(link) for link in set(links) }
	return [link_to_url[link] for link in links]

def download(url, times, fn):
	time.sleep(3)

	start, duration = times
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

def all_files_downloaded(fns):
	for fn in fns:
		if not file_downloaded(fn):
			return False

	return True

def file_downloaded(fn):
	if not os.path.exists(fn):
		return False

	vid = cv2.VideoCapture(fn)
	if vid.get(cv2.CAP_PROP_FRAME_COUNT) == 0:
		return False

	return True

def main():
	if len(sys.argv) != 2:
		print(f'usage: {sys.argv[0]} <inputfile>')
		return

	links, times, descs = readfile(sys.argv[1])
	urls = get_urls(links)
	fns = [f'{TMP_FN}_{i}.mp4' for i in range(len(times))]

	for url, time, desc, fn in zip(urls, times, descs, fns):
		print(f'--- {fn}')
		print(time[1], 'secs')
		print(desc)
		download(url, time, fn)

	while not all_files_downloaded(fns):
		for url, time, desc, fn in zip(urls, times, descs, fns):
			if file_downloaded(fn):
				continue

			print(f'--- retrying {fn}')
			print(time[1], 'secs')
			print(desc)
			download(url, time, fn)

	print('uploading')
	upload(fns, descs)

	for fn in fns:
		os.remove(fn)

if __name__ == '__main__':
	main()
