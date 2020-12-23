
## Setup
```
# install brew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
# install python 3 and pip 3
brew install python
# to convert Youtube mp4 to mp3 because Rekordbox can't export mp4s
brew install ffmpeg
# install dependencies
pip3 install --user -r requirements.txt
# install npm
brew install node
# install m3ugen https://github.com/sidlauskaslukas/m3u-generator
npm install -g m3u-generator

# to keep up to date you'll want to run
pip3 install --upgrade -r requirements.txt
# every so often
```

## Use
`python3 dl.py down -bearer <bearer-token> -pid <playlist-id> -dir <path-to-dir> -offset <offset>`

* `-bearer` - Go to Spotify's <a href="https://developer.spotify.com/console/get-playlist-tracks/?playlist_id=&market=&fields=&limit=&offset=&additional_types=" target="_blank">playground console</a> and click `Get Token`  to generate a bearer token
* `-pid` -  The id will be: `https://open.spotify.com/playlist/<id>?si=<ignore>` in the playlist link
* `-dir` - Path to directory playlist will be downloaded in ex: `~/house`
* `-offset` - Song # in the playlist after which all songs will be downloaded. Must be a multiple of 100 i.e. 100, 200, etc

The `.m3u` playlist file to import into rekordbox will be in the `-dir` above
