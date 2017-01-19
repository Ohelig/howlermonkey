# howlermonkey
howl.fm downloader

**Warning** - Code should be considered experimental and buggy. Pull requests are appreciated. 

## Usage

<pre>
$> cat playlistLinks.txt
http://howl.fm/audio/playlists/4656/friends-for-real-with-othello-clark
http://howl.fm/audio/playlists/4179/good-question
$> python ./howler.py ./playlistLinks.txt
</pre>

## TODO
* Write ID3 tags to .mp3 files

## Known Issues
* Right now, apostraphes in episode names get stripped. Working on fixing that for v0.1
* Playlists that have lots of episodes fail because the program doesn't wait for AJAX content to complete loading.
    i.e. Comedy Bang Bang (seems to use an API call though?): 
    <pre>GET http://dispatch.wolfpub.io/v1/episodes_for_show?show_id=4&client_id=711d9c80d73d4be3d3ed58af6135555e</pre>
    * Idea: Maybe have an option to parse from an .html file passed straight to BeautifulSoup
