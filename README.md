
## Setup
```
# install brew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
# install python 3 and pip
brew install python
# install dependencies
pip install --user -r requirements.txt
# install npm
brew install node
# install m3ugen https://github.com/sidlauskaslukas/m3u-generator
npm install -g m3u-generator
```

## Use
Add user python bins to path
MacOS: `export PATH="~/Library/Python/3.8/bin:$PATH"`

`python3 dl.py down -bearer <bearer-token> -pid <playlist-id> -dir <path-to-dir> -offset <offset>`

* `-bearer` - Go to https://developer.spotify.com/console/get-playlist-tracks/?playlist_id=&market=&fields=&limit=&offset=&additional_types= and click `Get Token`  to generate a bearer token and copy that
Go
* `-pid` -  The id will be: `https://open.spotify.com/playlist/<pid>?si=<some-other-id-you-dont-need>` in the playlist link
* `-dir` - Path to directory playlist will be downloaded in ex: `~/house`
* `-offset` - Song # in the playlist after which all songs will be downloaded. Must be a multiple of 100 i.e. 100, 200, etc

To generate a `.m3u` to import into rekordbox, run `m3ugen` in the `-dir` above
