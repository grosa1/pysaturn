# pysaturn
downloader for https://www.animesaturn.it/ 


How to use this script ---> {
    # move into pysaturn folder
    # launch the following command {python animesaturn_downloader.py  anime_saturn_link episodes_range}
    
    animesaturn_link: 
    must reference to the wanted anime home page (for example: https://www.animesaturn.it/anime/Made-in-Abyss-aszb )

    episodes_range:
    dependent on the range of episode of a particular anime.
    the format is the following {1-13}
    this will download 13 episodes.
    
    you can omit the episodes_range, the script will automatically download all the episodes 

    here a full example:
    {python animesaturn_downloader.py https://www.animesaturn.it/anime/Fullmetal-Alchemist-Brotherhood-ITA-aszb 1-64}


}


Bug Fixing --->{
    during the usege of this script bugs could occour. please report the bug you are exeperiencing
    here we will show some non-code dependet bug 

    1) Bug ---> [ from requests_html import HTMLSession ModuleNotFoundError: No module named 'requests_html' ] 

    1) Fix ---> use this command {pip install requests_html} and check you don't have any file named 'request.py'

}
