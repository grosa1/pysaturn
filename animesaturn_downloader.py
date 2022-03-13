import sys
import requests 
from bs4 import BeautifulSoup
from progress.bar import Bar
import re
import os
from requests_html import HTMLSession


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
  if ep_range:
    if ep_num < ep_range[0] or ep_num > ep_range[1]:
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

  source = None
  with HTMLSession() as session:
    r = session.get(stream_url)
    r.html.render()
    source = r.html.html

  mp4_url = re.findall(r'(https?://\S+.mp4)', source)
  if mp4_url:
    mp4_url = mp4_url[0]
    print(f"Downloading {mp4_url}")
    with open(ep_name + ".mp4", "wb") as outputf:
      response = requests.get(mp4_url, stream=True)
      assert response.status_code == 200
      outputf.write(response.content)
  else:
    playlist_url = None
    for u in re.findall(r'(https?://\S+)', source):
      u = u.replace("\"", "").replace(",", "")
      if u.endswith(".m3u8") and "(" not in u:
        playlist_url = u

    playlist_url = playlist_url.replace("playlist.m3u8", "480p/playlist_480p.m3u8")
    playlist = requests.get(playlist_url).text
    playlist_urls = list()
    for l in playlist.split("\n"):
      if l.endswith(".ts"):
        playlist_urls.append(playlist_url.replace("playlist_480p.m3u8", l))
    ep_name_tmp = ep_name + ".ts.temp"
    with open(ep_name_tmp, "wb") as outputf:
      n_parts = len(playlist_urls)
      print(f"Found {n_parts} parts")
      bar = Bar('Processing', max=n_parts)
      for i, pu in enumerate(playlist_urls):
        bar.next()
        response = requests.get(pu, stream=True)
        assert response.status_code == 200
        outputf.write(response.content)
      bar.finish()

    os.rename(ep_name_tmp, ep_name + ".ts")

    #os.system(f"ffmpeg -i {ep_name}.ts {ep_name}.mp4")
