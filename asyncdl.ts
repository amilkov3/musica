import * as fs from "fs";
import {
    headers
} from "../.pyenv/versions/playground/lib/python3.9/site-packages/bokeh/server/static/js/types/styles/tabs.css";
import {exec} from "child_process";
import util from "util"
import fetch from 'node-fetch';

const slsk = require("slsk-client");

const yargs = require(`yargs/yargs`);
const { hideBin } = require('yargs/helpers');
const argv = yargs(hideBin(process.argv)).argv;

const getTracks = async (): Promise<[string[], Set<string>]> => {
    const readFileAsync = util.promisify(fs.readFile)
    const fName = argv.dir.replace("~", "/Users/alex")
    console.log(`reading ${fName}`);
    const f = await readFileAsync(
        `${fName}/songs`,
        {
            encoding: 'utf-8'
        }
    );
    console.log(`reading cache`)
    const cache = new Set<string>();

    f.split(/\r?\n/).forEach(search =>  {
        cache.add(search)
    });

    const offset = argv.offset ?? 0

    const res = await fetch(
        `https://api.spotify.com/v1/playlists/${argv.pid}/tracks?market=ES&offset=${offset}`,
        {method: 'GET',
            headers: {
                Authorization: `Bearer ${argv.bearer}`,
                ContentType: 'application/json'
            }}
    ).then((res: any) => res.json(), (err) => {
        throw new Error(`spotify fetch ${err}`)
    })

    console.log(`res ${JSON.stringify(res)}`)

    const searches: string[] = []
    for (const i of res.items) {
        const artists = i.track.artists.map((a: any) => a.name).join(" ")
        const search = `${artists} ${i.track.name}`
        if (cache.has(search)) {
            continue
        }
        searches.push(search)
    }
    return [searches, cache]
}

interface SearchResult {
    size: number
    searchTerm: string
}

const search = async (cl: any, search: string): Promise<SearchResult | null> => {
    console.log(`search ${search}`)
    return new Promise((accept, rej) => cl.search({
        req: search,
        timeout: 3000
    }, (err: any, res: any) => {
        if (err) {
            console.log(`search for ${search} err: ${JSON.stringify(err)}`)
            return rej(err)
        }

        console.log(`search res ${JSON.stringify(res)}`)
        if (res.length == 0) {
            console.error(`no hit found for ${search}`)
            return accept(null)
        }
        accept(Object.assign(res[0], {searchTerm: search}))
    }))
}

const download = async (
    cl: any,
    file: SearchResult
): Promise<void> => {
    return new Promise((accept, rej) => {
        let sent = 0
        //const totalData: any[] = []
        cl.download({
            file,
            path: `${argv.dir}/${file.searchTerm}.mp3`
        }, (err: any, data: any) => {
            if (err) {
                console.log(`download ${JSON.stringify(file)} err ${JSON.stringify(err)}`)
                return rej(err)
            }
            sent += data.buffer.length
            //totalData.push(...data.buffer)
            console.log(`prog ${sent}/${file.size}`)
            if (sent >= file.size) {
                console.log(`successfully downloaded ${file.searchTerm}`)
                fs.writeFile(`${argv.dir}/songs`, file.searchTerm, (err) => {
                    if (err) return rej(err)
                    console.log(`cached ${file.searchTerm}`)
                    accept()
                    return
                })
            }
        })
    })
}

const downloadChunk = async (cl: any, chunk: string[]) => {
    // @ts-ignore
    const searches: SearchResult[] =  (await Promise.all(
        chunk.map((track) => search(cl, track))
    )).filter((res) => !!res)

    console.log(`chunk search results ${searches.length}`)
    return Promise.all(searches.map((res) => download(cl, res)))
}


(async () => {

    const cl = await new Promise((res, rej) => {
        const user = (Math.random() + 1).toString(36).substring(2);
        const pass = (Math.random() + 1).toString(36).substring(2);
        slsk.connect({user, pass, timeout: 3000}, (err: any, client: any) => {
            if (err) {
                console.log(`err ${err}`)
                rej(err)
            }
            console.log(`client ${JSON.stringify(client)}`)
            res(client)
        })
    })

    const [tracks, cache] = await getTracks();

    const chunkSize = 100;
    for (let i = 0; i < tracks.length; i += chunkSize) {
        const chunk = tracks.slice(i, i + chunkSize);
        console.log(`downloading chunk ${chunk.length}`);
        await downloadChunk(cl, chunk)
        console.log(`downloaded chunk ${chunk.length}`)
    }

    exec(
        'm3ugen',
        {cwd: argv.dir},
        (err, stdout, stderr) => {
        if (err) {
            console.log(`m3ugen err ${JSON.stringify(err)}`)
            console.log(`m3ugen stderr ${stderr}`)
            return
        }
        console.log(stdout)
    })

})();
