import http.client
import json
import os
from youtubesearchpython import SearchVideos
import argparse
import editdistance

def main(spotify_bearer, pid, out_dir, offset):
    out_dir = out_dir.rstrip('/')
    if not os.path.exists(f'{out_dir}'):
        os.makedirs(f'{out_dir}')
    with open(f'{out_dir}/songs', 'a+') as f:
        f.seek(0, 0)
        m = set({})
        for line in f.readlines():
            m.add(line.rstrip())
        headers1 = {'Authorization': f'Bearer {spotify_bearer}', 'Content-type': 'application/json'}
        cont = True
        j = 0
        while cont:
            s = http.client.HTTPSConnection("api.spotify.com")
            offset1 = j * 100
            if offset:
                offset1 = offset
            path = f'/v1/playlists/{pid}/tracks?market=ES&offset={offset1}'
            s.request("GET", path , headers=headers1)
            r1 = s.getresponse()
            code = r1.getcode()
            if code != 200:
                print(f'Got {code}. Probably a 401. Get a new bearer token and try again...madafaaaaka')
                return
            x1 = json.loads(r1.read().decode())
            if len(x1["items"]) < 100:
                cont = False
            for i in x1["items"]:
                try:
                    artists = " ".join([a["name"] for a in i["track"]["artists"]])
                    search = f'{artists} {i["track"]["name"]}'#.replace(" ", "%20")
                    if search in m:
                        print(f'Already downloaded {search}. Skipping')
                        continue
                    print(f'Searching for {search}')
                    r = SearchVideos(search, offset = 1, mode = "json", max_results = 20)
                    x = json.loads(r.result())
                    if len(x["search_result"]) == 0:
                        print(f'no search results for {search}')
                        continue
                    id1 = x["search_result"][0]["id"]
                    res = os.system(f'youtube-dlc -o \"{out_dir}/%(title)s.%(ext)s\" https://www.youtube.com/watch?v={id1}')
                    if res == 0:
                        f.write(f'{search}\n')
                except Exception as e:
                   print(f'caught exception: {e}')
            j += 1

def clean(out_dir):
    files = os.listdir(out_dir)
    for filename1 in files:
        filename11 = filename1
        if len(filename1) > 16 and filename1[-16] == '-':
            filename11 = filename1[:-16]
        else:
            filename11 = filename1[:-4]
        s1 = filename11.split('-')
        if len(s1) < 2 or len(s1[1]) == 0:
            continue
        songname1 = s1[1]
        #s1 = filename1.split('-')[-1].split('.')[0]
        #if len(s1) < 2:
        #    continue
        #except Exception as e:
        for filename2 in files:
            if filename1 == filename2:
                continue
            #s2 = filename2.split('-')
            #if len(s2) < 2:
            #    continue
            filename21 = filename2
            if len(filename2) > 16 and filename2[-16] == '-':
                filename21 = filename2[:-16]
            else:
                filename21 = filename2[:-4]
            s2 = filename21.split('-')
            if len(s2) < 2 or len(s2[1]) == 0:
                continue
            songname2 = s2[1]
            #s2 = filename2.split('-')[-1].split('.')[0]
            v = editdistance.eval(songname1, songname2)
            #print(s1[1][:6], s2[1][:6])
            #s1[1][:6] == s1[1][:6]
            #songname1[:5] == songname2[:5] and

            if abs(len(songname1) - len(songname2)) < 5 and v/len(songname1) < .2:
                print(f'Match {songname1}  {songname2}')
                try:
                    os.remove(f'{out_dir}/{filename2}')
                except Exception as e:
                    pass



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download some music')
    parser.add_argument('down', nargs='?')
    parser.add_argument('clean', nargs='?')
    parser.add_argument('-bearer', type=str)
    parser.add_argument('-pid', type=str)
    parser.add_argument('-dir', type=str)
    parser.add_argument('-offset', type=int)

    args = parser.parse_args()

    print(args.down, args.bearer, args.pid, args.dir)

    if args.down and args.bearer and args.pid and args.dir:
        print('foo')
        main(args.bearer, args.pid, args.dir, args.offset)
    elif args.clean and args.dir:
        clean(args.dir)