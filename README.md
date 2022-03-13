# pysaturn
downloader for https://www.animesaturn.it/ 


### How to use
Clone the pysaturn repository and launch the following commands:
 
```
python3 -m pip install -r requirements.txt

python3 animesaturn_downloader.py <anime_saturn_link> <episodes-range>
```

Where:

`animesaturn_link`: must reference to the wanted anime home page (for example: https://www.animesaturn.it/anime/Made-in-Abyss-aszb )

`episodes_range`: dependent on the range of episode of a particular anime.
For example, to download the first 13 episodes, you can use the following param: `1-13`
The script will automatically download all the episodes if you omit the `episodes_range` param.

### Usage example
```python3 animesaturn_downloader.py https://www.animesaturn.it/anime/Fullmetal-Alchemist-Brotherhood-ITA-aszb```

or 

```python3 animesaturn_downloader.py https://www.animesaturn.it/anime/Fullmetal-Alchemist-Brotherhood-ITA-aszb 1-13```
