import sys
import requests 
from bs4 import BeautifulSoup
import re
import os


#https://www.animesaturn.it/anime/Fullmetal-Alchemist-Brotherhood-ITA-aszb

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <url> <episodes-range>")
    sys.exit(1)

main_url = sys.argv[1]
ep_range = None
if len(sys.argv) > 2:
    ep_range = sys.argv[2].split("-")
    ep_range[0] = int(ep_range[0])
    ep_range[1] = int(ep_range[1])

response = requests.get(main_url)
soup = BeautifulSoup(response.text, 'html.parser') 
links = [l.get('href') for l in soup.find_all('a', class_="bottone-ep")]
print(f"Found {len(links)} links")

for link in links:
  ep_name = link.split('/')[-1]

  ep_num = int(ep_name.split('-')[-1])
  if ep_range and ep_num < ep_range[0] or ep_num > ep_range[1]:
    print(f"Skipping {ep_name}")
    continue

  print(f"Processing {ep_name}")
  response = requests.get(links[0])
  soup = BeautifulSoup(response.text, 'html.parser') 

  stream_url = None
  for l in soup.find_all('a'):
    url = l.get('href')
    if "watch?file=" in url:
      stream_url = url

  s = requests.get(stream_url).text
  playlist_url = None
  for u in re.findall(r'(https?://\S+)', s):
    u = u.replace("\"", "").replace(",", "")
    if u.endswith(".m3u8") and "(" not in u:
      playlist_url = u

  playlist_url = playlist_url.replace("playlist.m3u8", "480p/playlist_480p.m3u8")
  playlist = requests.get(playlist_url).text
  playlist_urls = list()
  for l in playlist.split("\n"):
    if l.endswith(".ts"):
      playlist_urls.append(playlist_url.replace("playlist_480p.m3u8", l))

  with open(ep_name + ".ts", "wb") as outputf:
    n_parts = len(playlist_urls)
    print(f"Found {n_parts} parts")
    for i, pu in enumerate(playlist_urls):
      print(f"Downloading part {i+1} of {n_parts}")
      response = requests.get(pu)
      assert response.status_code == 200
      outputf.write(response.content)

  os.system(f"ffmpeg -i {ep_name}.ts {ep_name}.mp4")