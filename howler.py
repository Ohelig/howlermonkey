import argparse
import os
import subprocess
import HTMLParser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from BeautifulSoup import BeautifulSoup
from selenium import webdriver


def cleanString(dirty):
    if isinstance(dirty, str):
        # Convert to UTF-8
        dirty = dirty.encode('utf-8')

    # Unescape html entities
    dirty = dirty.replace("%2520", " ").replace("%22", "").replace("&#039;", "'")
    clean = h.unescape(dirty)

    return clean

# Instantiate the parser
parser = argparse.ArgumentParser(description='Download podcasts from Howl.fm')

# Add file arg
parser.add_argument('playlistFile', type=file,
                    help='A file containing playlist urls to download')

# Add verbose switch
parser.add_argument('-v', '--verbose', action='store_true', required=False, help='Verbose mode. (PhantomJS logs to ghostdriver.log)')

# Parse the args
args = parser.parse_args()

# Set verbose flag
verbose = args.verbose

# Create the driver
phantomPath = '/usr/local/lib/node_modules/phantomjs-prebuilt/lib/phantom/bin/phantomjs'
if verbose:
    # Create ghostdriver.log
    driver = webdriver.PhantomJS(executable_path=phantomPath)
else:
    # Set log destination to /dev/null
    driver = webdriver.PhantomJS(executable_path=phantomPath,service_log_path=os.path.devnull)
driver.set_window_size(1024, 768) # optional

# Instantiate the HTMLParser
h = HTMLParser.HTMLParser()

with args.playlistFile as f:
    for playlistUrl in f:
        print("Parsing playlist: " + playlistUrl)

        driver.get(playlistUrl)
        print("   Waiting for page to load...")
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "all-episodes")))
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "episode-row")))
        html = driver.page_source
        soup = BeautifulSoup(html)

        foundEpisodes = False

        # Parse the HTML
        episodeRows = soup.table(attrs={'class': 'episode-row'})
        numEpisodes = len(list(episodeRows))
        episodesTable = soup.table
        episodeExpandRows = episodesTable(attrs={'class': 'episode-expand-row'})
        showTitle = soup.find(attrs={'class': 'show-title'}).string
        showTitle = cleanString(showTitle)
        showDesc = soup(attrs={'class': 'desc'})[0].text
        showCoverLink = soup(attrs={'class': 'img-responsive'})[0]['src']

        # Instantiate an episode dictionary. All episodes will be stored here
        episodes = {}

        # Parse HTML
        i = 0
        for row in episodeRows:
            episode = {}
            episode['name'] = row.find(attrs={'class': 'episode-title'}).text

            if row.find(attrs={'class': 'episode-length'}) is not None:
                episode['length'] = row.find(attrs={'class': 'episode-length'}).text
            else:
                episode['length'] = 'Unknown runtime'

            episode['link'] = row.find(attrs={'class': 'episode-play'}).a['data-stream-url']

            if len(list(episodeExpandRows[i].findAll('p'))) >= 2:
                episode['description'] = episodeExpandRows[i].findAll('p')[1].text
            else:
                episode['description'] = episodeExpandRows[i].text

            # Find .episode-date elements. There can be 1 if just an episode date, or 2
            # if an episode date and an episode number. BeautifulSoup doesn't seem to have
            # a len(findResults) method so just loop through them and count them
            episodeDates = row(attrs={'class': 'episode-date'})
            j = 0
            for td in episodeDates:
                j += 1
            if j == 1:
                # Just an episode date. No number
                episode['date'] = row.find(attrs={'class': 'episode-date'}).text
                episode['number'] = ""
            elif j == 2:
                # Both episode number and date exist
                episode['number'] = row.findAll(attrs={'class': 'episode-date'})[0].text
                episode['date'] = row.findAll(attrs={'class': 'episode-date'})[1].text
            else:
                episode['date'] = ""
                episode['number'] = ""

            # Add episode to list of episodes
            episodes[i] = episode
            i += 1

        print("   Found " + str(numEpisodes) + " episodes")
        print("   Creating show folder...")

        # Create show folder
        showDirectory = showTitle.replace('/', ' ') + "/"
        if not os.path.exists(showDirectory):
            os.makedirs(showDirectory)

        # Write show info to showInfo.txt and keep the tab open
        f = open(showDirectory + "showInfo.txt", 'w')
        f.write(showTitle + "\n" + "\t" + showDesc + "\n\n")

        # Download show cover image
        print("   Downloading show cover...")
        procString = "wget --quiet '" + showCoverLink + "' -O " + '"' + showDirectory + showCoverLink.split("/")[
            len(showCoverLink.split("/")) - 1] + '"'
        wgetProc = subprocess.Popen(procString, stdout=subprocess.PIPE, shell=True)

        # One download at a time or the output gets all messed up
        wgetProc.wait()

        # Print download result
        if wgetProc.stderr is None:
            print("     Success\n")
        else:
            print("     Error: " + wgetProc.stderr)

        # For every episode of this show, do the following
        for index in range(len(episodes)):
            episode = episodes[index]

            if episode['link'] == 'null':
                print("   Downloading (" + str(index + 1) + "/" + str(len(episodes)) + "):")
                print('      Error: No .mp3 link for this episode. Skipping...')
                continue

            # Parse filename
            if "filename=" in episode['link'] and "%22&" in episode['link']:
                filename = cleanString(episode['link'].split("filename=")[1].split("%22&")[0])
            else:
                # The link does not have the filename parameter. Use the episode name
                filename = episode['name'] + '.mp3'

            # If the show listed episode numbers, add them to the filename
            if episode['number'] != "":
                filename = episode['number'] + " - " + filename
                f.write(episode['number'] + " - ")

            print("   Downloading (" + str(index + 1) + "/" + str(len(episodes)) + "): " + filename + "...")

            episodeLine = episode['name'] + " - " + episode['date'] + " - " + episode['length'] + "\n\t" + episode[
                'description'] + "\n\n"
            f.write(cleanString(episodeLine).encode('utf-8'))

            # Prepare the wget string and execute
            procString = "wget --no-clobber --quiet '" + episode['link'] + "' -O " + '"' + showDirectory + filename + '"'
            wgetProc = subprocess.Popen(procString, stdout=subprocess.PIPE, shell=True)

            # One download at a time or the output gets all messed up
            wgetProc.wait()

            # Print download result
            if wgetProc.stderr is None:
                print("     Success")
            else:
                print("     Error: " + wgetProc.stderr)

print("\n All done downloading!")
