[![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

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

## Requirements
* selenium, BeautifulSoup
   * <code>pip install selenium BeautifulSoup</code>
* NodeJS
* PhantomJS - Edit the path in the script to point at your executable
   * <code>npm -g install phantomjs-prebuilt</code> 
   * or 
   * <code>brew install phantomjs</code> 

## TODO
* Write ID3 tags to .mp3 files

## Known Issues
* Apostrophes in episode names currently get stripped

## License 
[Creative Commons Attribution-NonCommercial 4.0 International](https://creativecommons.org/licenses/by-nc/4.0/)
