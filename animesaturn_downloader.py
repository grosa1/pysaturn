from operator import contains
import sys
from tkinter import W
import requests 
from bs4 import BeautifulSoup
import re
import os
from requests_html import HTMLSession
import traceback
import time

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s')
logging.getLogger('requests_html').setLevel(logging.WARNING)


DOWNLOAD_MAX_RETRIES = 3
SLEEP_SECONDS_ON_ERROR = 3
STREAM_RESOLUTION = "480p"
#STREAM_RESOLUTION = "720p"

WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

def render_player_page(player_page_url: str) -> str:
  retries = 0
  try:
    with HTMLSession() as session:
      r = session.get(player_page_url)
      r.html.render()
      source = r.html.html
      assert source is not None
      return source
  except Exception as e:
    retries += 1
    if retries > DOWNLOAD_MAX_RETRIES:
      logging.error(traceback.print_exc())
    else:
      logging.warning(FAIL + f"Error while rendering page {player_page_url}, retrying..." + ENDC)
      time.sleep(SLEEP_SECONDS_ON_ERROR)
      return render_player_page(player_page_url)


def download_resource(resource_url: str):
  retries = 0
  try:
    response = requests.get(resource_url, timeout=10)
    assert response.status_code == 200
    return response.content
  except Exception as e:
    retries += 1
    if retries > DOWNLOAD_MAX_RETRIES:
      logging.error(traceback.print_exc())
    else:
      logging.warning(FAIL + f"Error while downloading {resource_url}, retrying..." + ENDC)
      time.sleep(SLEEP_SECONDS_ON_ERROR)
      return download_resource(resource_url)


def is_episode_alredy_present(out_dir:str , ep_number: int) -> bool :
  script_dir = os.getcwd()
  try:
    os.chdir(out_dir)
    for file in os.listdir():
      if(not os.path.isdir(file) and file.split(".")[-1] != "temp" and file.split('-')[-1].split(".")[0] == str(ep_number)):
        os.chdir(script_dir)
        return True
  except:
    print(WARNING + f"/{out_dir} directory not found, impossible perform duplicate episodes checking" + ENDC)

  os.chdir(script_dir)
  return False
    

def main(main_url: str, ep_range_start: int, ep_range_end: int):
  out_dir = main_url.split('/')[-1]
  if not os.path.exists(out_dir):
    os.mkdir(out_dir)

  response = requests.get(main_url)
  soup = BeautifulSoup(response.text, 'html.parser') 
  links = [l.get('href') for l in soup.find_all('a', class_="bottone-ep")]
  logging.info(f"Found {len(links)} episode links")

  for link in links:
    ep_name = link.split('/')[-1]
    ep_name_dest = os.path.join(out_dir, ep_name)
    ep_num = int(ep_name.split('-')[-1])

    if is_episode_alredy_present(out_dir, ep_num) or (
      (ep_range_start and ep_range_end ) and 
      (ep_num < ep_range_start or ep_num > ep_range_end)):
      logging.info(f"Skipping {ep_name}")
      continue

    logging.info(f"Processing {ep_name}")
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser') 

    player_page_url = None
    for l in soup.find_all('a'):
      url = l.get('href')
      if "watch?file=" in url:
        player_page_url = url

    source = render_player_page(player_page_url)

    # look for mp4 stream or else m3u8 stream
    mp4_url = re.findall(r'(https?://\S+.mp4)', source)
    if mp4_url:
      mp4_url = mp4_url[0]
      logging.info(f"Downloading {mp4_url}")
      ep_name_tmp = ep_name_dest + ".mp4.temp"
      with open(ep_name_tmp, "wb") as output_buffer:
        output_buffer.write(download_resource(mp4_url))
      os.rename(ep_name_tmp, ep_name_dest + ".mp4")
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
      ep_name_tmp = ep_name_dest + ".ts.temp"
      with open(ep_name_tmp, "wb") as output_buffer:
        n_parts = len(playlist_urls)
        logging.info(f"Found {n_parts} parts")
        for i, pu in enumerate(playlist_urls):
          logging.info(f"Downloading part {i+1} of {n_parts}")
          output_buffer.write(download_resource(pu))
      os.rename(ep_name_tmp, ep_name_dest + ".ts")


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print(f"USAGE: python3 {sys.argv[0]} <url> <episodes-range>")
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
