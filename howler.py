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
    # Convert to UTF-8
    cleaner = dirty.encode('utf8')

    # Unescape html entities
    cleaner = cleaner.replace("%2520", " ").replace("%22", "").replace("&#039;", "'")
    clean = h.unescape(cleaner)

    return clean


# Create the driver
driver = webdriver.PhantomJS(executable_path='/usr/local/lib/node_modules/phantomjs-prebuilt/lib/phantom/bin/phantomjs')
driver.set_window_size(1024, 768) # optional
#driver.get('https://google.com/')
#driver.save_screenshot('screen.png') # save a screenshot to disk

# Instantiate the parser
parser = argparse.ArgumentParser(description='Download podcasts from Howl.fm')

# Add arg
parser.add_argument('--mode', required=True, help='Parsing mode: list/source')
parser.add_argument('playlistFile', type=file,
                    help='If mode=list: A file containing playlist urls to download\n If mode=source, a file '
                         'containing the source code of a playlist to parse')
# parser.add_argument('playlistSource', type=file, help='A file containing the source code of a playlist to parse')

# Parse the args
args = parser.parse_args()

# Instantiate the HTMLParser
h = HTMLParser.HTMLParser()

if args.mode == "list":
    with args.playlistFile as f:
        for playlistUrl in f:
            print("Parsing playlist: " + playlistUrl)

            # Make a GET request and parse the html into soup
            # response = requests.get(playlistUrl)
            # soup = BeautifulSoup(response.text)

            driver.get(playlistUrl)
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

            print "   Found " + str(numEpisodes) + " episodes"
            print "   Creating show folder..."

            # Create show folder
            showDirectory = showTitle + "/"
            if not os.path.exists(showDirectory):
                os.makedirs(showDirectory)

            # Write show info to showInfo.txt and keep the tab open
            f = open(showDirectory + "showInfo.txt", 'w')
            f.write(showTitle + "\n" + "\t" + showDesc + "\n\n")

            # Download show cover image
            print "   Downloading show cover..."
            procString = "wget --quiet '" + showCoverLink + "' -O " + '"' + showDirectory + showCoverLink.split("/")[
                len(showCoverLink.split("/")) - 1] + '"'
            wgetProc = subprocess.Popen(procString, stdout=subprocess.PIPE, shell=True)

            # One download at a time or the output gets all messed up
            wgetProc.wait()

            # Print download result
            if wgetProc.stderr is None:
                print "     Success\n"
            else:
                print "     Error: " + wgetProc.stderr

            # For every episode of this show, do the following
            for index in range(len(episodes)):
                episode = episodes[index]

                # Parse filename
                filename = cleanString(episode['link'].split("filename=")[1].split("%22&")[0])

                # If the show listed episode numbers, add them to the filename
                if episode['number'] != "":
                    filename = episode['number'] + " - " + filename
                    f.write(episode['number'] + " - ")

                print("   Downloading (" + str(index + 1) + "/" + str(len(episodes)) + "): " + filename + "...")

                episodeLine = episode['name'] + " - " + episode['date'] + " - " + episode['length'] + "\n\t" + episode[
                    'description'] + "\n\n"
                f.write(cleanString(episodeLine))

                # Prepare the wget string and execute
                procString = "wget --quiet '" + episode['link'] + "' -O " + '"' + showDirectory + filename + '"'
                wgetProc = subprocess.Popen(procString, stdout=subprocess.PIPE, shell=True)

                # One download at a time or the output gets all messed up
                wgetProc.wait()

                # Print download result
                if wgetProc.stderr is None:
                    print("     Success")
                else:
                    print("     Error: " + wgetProc.stderr)

    print("\n All done downloading!")
elif args.mode == "source":
    print ("Parsing podcast episodes from source code file...")
else:
    print("Error: Unknown mode")
