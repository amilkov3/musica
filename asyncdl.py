import http.client
import json
import os
from typing import List, Tuple

from youtubesearchpython import SearchVideos
import argparse
import editdistance
import subprocess
import re
import sys
from iytdl import iYTDL
import asyncio
import logging

def read_cache(f):
    f.seek(0, 0)
    m = set({})
    for line in f.readlines():
        m.add(line.rstrip())
    return m

async def download(
    f,
    dir,
    chunk: List[str]
) -> List[str]:
    async with iYTDL(
        log_group_id=0,
        cache_path=dir,
        download_path=dir
    ) as ytdl:
        title_to_search = {}
        def prog_func(dict):
            total = dict["total_bytes_estimate"] if "total_bytes_estimate" in dict else '<>'
            status = dict['status']
            title = dict["info_dict"]["title"]
            logging.info(f'{status} {title} {dict["downloaded_bytes"]}/{total}')
            if status == 'finished':
                search = title_to_search[title]
                logging.info(f'caching {search}')
                f.write(f'{search}\n')
            pass

        success = []
        for search in chunk:
            logging.info(f'searching for {search}')
            try:
                r = SearchVideos(search, offset = 1, mode = "json", max_results = 20)
                res = json.loads(r.result())
                if len(res["search_result"]) == 0:
                    logging.error(f'no search results for {search}')
                    continue
                res_i = 0
                link = res["search_result"][res_i]['link']
                title = res["search_result"][res_i]['title']
                title_to_search[title] = search
                status_code = await ytdl.audio_downloader(
                    link,
                    search,
                    "",
                    prog_func,
                )
                if status_code != 0:
                    logging.error(f'failed downloading {search} status {status_code}')
                    continue
                logging.info(f'successfully downloaded ${search}')
                success.append(search)
            except Exception as e:
                logging.error(f'exception downloading {search}: {e}')

        return success

def get_tracks(spotify_bearer, pid, out_dir, offset, use_min_dist):
    out_dir = out_dir.rstrip('/')
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    searches = []
    with open(f'{out_dir}/songs', 'a+') as f:
        cache = read_cache(f)
        cont = True
        offset = offset if offset else 0
        while cont:
            s = http.client.HTTPSConnection("api.spotify.com")
            path = f'/v1/playlists/{pid}/tracks?market=ES&offset={offset}'
            s.request("GET", path , headers={
                'Authorization': f'Bearer {spotify_bearer}',
                'Content-type': 'application/json'
            })
            res = s.getresponse()
            code = res.getcode()
            if code != 200:
                logging.error(f'Got {code}. Probably a 401. Get a new bearer token and try again...madafaaaaka')
                return
            items = json.loads(res.read().decode())
            if len(items["items"]) < 100:
                cont = False
            for i in items["items"]:
                artists = " ".join([a["name"] for a in i["track"]["artists"]])
                search = f'{artists} {i["track"]["name"]}'#.replace(" ", "%20")
                if search in cache:
                    continue
                searches.append(search)
            offset += 100
        logging.info(f'downloading {len(searches)} songs')
        return searches, cache

async def main(bearer_token, pid, out_dir, offset, use_min_dist):
    tracks, cache = get_tracks(
        bearer_token,
        pid,
        out_dir,
        offset,
        use_min_dist
    )
    chunks = []
    n = 100
    for i in range(0, len(tracks), n):
        chunks.append(tracks[i:i + n])
    with open(f'{args.dir}/songs', 'a+') as f:
        tasks = []
        for i, c in enumerate(chunks):
            logging.info(f'downloading chunk {i}')
            t = asyncio.create_task(download(f, out_dir, c))
            tasks.append(t)
        a = await asyncio.gather(*tasks)
        logging.info('finished downloading everything')
    p = subprocess.Popen(['m3ugen'], cwd=out_dir)
    p.wait()

# TODO: finish
#def clean(out_dir):
#    files = os.listdir(out_dir)
#    for filename1 in files:
#        filename11 = filename1
#        if len(filename1) > 16 and filename1[-16] == '-':
#            filename11 = filename1[:-16]
#        else:
#            filename11 = filename1[:-4]
#        s1 = filename11.split('-')
#        if len(s1) < 2 or len(s1[1]) == 0:
#            continue
#        songname1 = s1[1]
#        #s1 = filename1.split('-')[-1].split('.')[0]
#        #if len(s1) < 2:
#        #    continue
#        #except Exception as e:
#        for filename2 in files:
#            if filename1 == filename2:
#                continue
#            #s2 = filename2.split('-')
#            #if len(s2) < 2:
#            #    continue
#            filename21 = filename2
#            if len(filename2) > 16 and filename2[-16] == '-':
#                filename21 = filename2[:-16]
#            else:
#                filename21 = filename2[:-4]
#            s2 = filename21.split('-')
#            if len(s2) < 2 or len(s2[1]) == 0:
#                continue
#            songname2 = s2[1]
#            #s2 = filename2.split('-')[-1].split('.')[0]
#            v = editdistance.eval(songname1, songname2)
#            #print(s1[1][:6], s2[1][:6])
#            #s1[1][:6] == s1[1][:6]
#            #songname1[:5] == songname2[:5] and
#
#            if abs(len(songname1) - len(songname2)) < 5 and v/len(songname1) < .2:
#                print(f'Match {songname1}  {songname2}')
#                try:
#                    os.remove(f'{out_dir}/{filename2}')
#                except Exception as e:
#                    pass



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download some music')
    parser.add_argument('down', nargs='?')
    #parser.add_argument('clean', nargs='?')
    parser.add_argument('-bearer', type=str)
    parser.add_argument('-pid', type=str)
    parser.add_argument('-dir', type=str)
    parser.add_argument('-offset', type=int)
    parser.add_argument('-min_dist', default=False, action='store_true')

    args = parser.parse_args()

    logging.basicConfig(
        stream=sys.stdout,
        #filename=f'{args.dir}/log',
        encoding='utf-8',
        level=logging.INFO
    )
    logging.info(f'Running with args: bearer: {args.bearer}, pid: {args.pid}, dir: {args.dir}, min_dist: {args.min_dist}')

    b = subprocess.check_output(['python3', '--version']).decode("utf-8")
    p = re.compile("Python 3\.([1-9]{1})\.[1-9]{1}")
    match = p.match(b)
    if not match:
        raise Exception(f'invalid python version: {b}')
    if len(match.groups()) != 1:
        raise Exception("invalid match")
    v = f'3.{match.groups()[0]}'
    logging.info(f'Python major/minor version: {v}')
    os.system(f'export PATH="~/Library/Python/{v}/bin:$PATH"')

    commands = {
        'yt-dlp': "youtube-dlc not found in path",
        'm3ugen': "make sure you've installed m3u-generator"
    }
    for c, r in commands.items():
        if os.system(f'command -v {c} &> /dev/null') != 0:
            raise Exception(f'command {c} not found: {r}')

    if args.down and args.bearer and args.pid and args.dir:
        offset = 0
        if args.offset:
            if len(str(args.offset)) != 3:
                raise Exception("offset must be multiple of 100")
            offset = int(str(args.offset)[0]) * 100
        asyncio.run(main(args.bearer, args.pid, args.dir, offset, args.min_dist))

    #elif args.clean and args.dir:
    #    clean(args.dir)
