import sys
import requests 
from bs4 import BeautifulSoup
from progress.bar import Bar
import re
import os
from requests_html import HTMLSession
import traceback


DOWNLOAD_MAX_RETRIES = 3
STREAM_RESOLUTION = "480p"
#STREAM_RESOLUTION = "720p"


def download_resource(resource_url: str):
  retries = 0
  try:
    response = requests.get(resource_url, stream=True)
    assert response.status_code == 200
    return response.content
  except Exception as e:
    retries += 1
    if retries > DOWNLOAD_MAX_RETRIES:
      traceback.print_exc()
    else:
      download_resource(resource_url)


def main(main_url: str, ep_range_start: int, ep_range_end: int):
  out_dir = main_url.split('/')[-1]
  if not os.path.exists(out_dir):
    os.mkdir(out_dir)

  response = requests.get(main_url)
  soup = BeautifulSoup(response.text, 'html.parser') 
  links = [l.get('href') for l in soup.find_all('a', class_="bottone-ep")]
  print(f"Found {len(links)} episode links")

  for link in links:
    ep_name = link.split('/')[-1]
    ep_name = os.path.join(out_dir, ep_name)

    ep_num = int(ep_name.split('-')[-1])
    if ep_range:
      if ep_num < ep_range_start or ep_num > ep_range_end:
        print(f"Skipping {ep_name}")
        continue

    print(f"Processing {ep_name}")
    response = requests.get(links[0])
    soup = BeautifulSoup(response.text, 'html.parser') 

    stream_page_url = None
    for l in soup.find_all('a'):
      url = l.get('href')
      if "watch?file=" in url:
        stream_page_url = url

    source = None
    with HTMLSession() as session:
      r = session.get(stream_page_url)
      r.html.render()
      source = r.html.html

    # look for mp4 stream or else m3u8 stream
    mp4_url = re.findall(r'(https?://\S+.mp4)', source)
    if mp4_url:
      mp4_url = mp4_url[0]
      print(f"Downloading {mp4_url}")
      ep_name_tmp = ep_name + ".mp4.temp"
      with open(ep_name_tmp, "wb") as output_buffer:
        output_buffer.write(download_resource(mp4_url))
      os.rename(ep_name_tmp, ep_name + ".mp4")
    else:
      # look for the stream playlist url
      stream_playlist_url = None
      for u in re.findall(r'(https?://\S+)', source):
        u = u.replace("\"", "").replace(",", "")
        if u.endswith(".m3u8") and "(" not in u:
          stream_playlist_url = u

      # extract video segments
      stream_playlist_url = stream_playlist_url.replace("playlist.m3u8", f"{STREAM_RESOLUTION}/playlist_{STREAM_RESOLUTION}.m3u8")
      playlist = requests.get(stream_playlist_url).text
      playlist_urls = list()
      for line in playlist.split("\n"):
        if line.endswith(".ts"):
          playlist_urls.append(stream_playlist_url.replace(f"playlist_{STREAM_RESOLUTION}.m3u8", line))

      # download all video segments and merge them in a buffer file
      ep_name_tmp = ep_name + ".ts.temp"
      with open(ep_name_tmp, "wb") as output_buffer:
        n_parts = len(playlist_urls)
        print(f"Found {n_parts} parts")
        bar = Bar('Processing', max=n_parts)
        for i, pu in enumerate(playlist_urls):
          bar.next()
          output_buffer.write(download_resource(pu))
        bar.finish()
      os.rename(ep_name_tmp, ep_name + ".ts")


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <url> <episodes-range>")
    sys.exit(1)

  main_url = sys.argv[1]
  assert main_url is not None

  ep_range_start = None
  ep_range_end = None
  if len(sys.argv) > 2:
    ep_range = sys.argv[2].split("-")
    ep_range_start = int(ep_range[0])
    ep_range_end = int(ep_range[1])
    assert ep_range_start is not None and ep_range_end is not None

  main(main_url, ep_range_start, ep_range_end)