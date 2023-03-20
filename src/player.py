from playsound import playsound
from time import sleep
import threading
import json
from datetime import datetime, timedelta
import time
from prettytable import PrettyTable
from os import system, name, get_terminal_size
import json
import requests


NEXT_TRACKS_TO_DISPLAY = get_terminal_size()[1] - 7
'''
Set to terminal height minus 7\n
subtract Prev and Current Track lines (2)
and 3 Lines for Header and 2 for footer
'''

PLAYLIST_FILE = 'playlist.txt'
CUTS_DB_FILE  = 'cuts.json'
PAD_OUT_FILE  = 'pad.json'

'''Send PAD to BreakawayOne via HTTP API'''
ENABLE_BA1_PAD = False
PAD_HOST = '127.0.0.1'
PAD_PORT = 8282
PAD_PROC = 'hd3'


class PlaylistTable:
    def __init__(self):
        self.table = PrettyTable()
        self.table.field_names = ["AIR TIME", "CUT ID",
                                  "CATEGORY", "TITLE", "ARTIST", "LENGTH", "INTRO"]
        self.color = {} 
        self._init_colors()

        self.bg = {}
        self._init_backgrounds()

        self.style = {}
        self._init_styles()

        self.end_format = '\033[0m'

        self.air_time_counter = 0

    def _init_colors(self) -> None:
        self.color['black'] = '\033[90m'
        self.color['red'] = '\033[91m'
        self.color['green'] = '\033[92m'
        self.color['yellow'] = '\033[93m'
        self.color['blue'] = '\033[94m'
        self.color['purple'] = '\033[95m'
        self.color['cyan'] = '\033[96m'
        self.color['gray'] = '\033[97m'

    def _init_backgrounds(self) -> None:
        self.bg['black'] = '\033[40m'
        self.bg['red'] = '\033[41m'
        self.bg['green'] = '\033[42m'
        self.bg['orange'] = '\033[43m'
        self.bg['blue'] = '\033[44m'
        self.bg['purple'] = '\033[45m'
        self.bg['cyan'] = '\033[46m'
        self.bg['gray'] = '\033[47m'

    def _init_styles(self) -> None:
        self.style['bold'] = '\033[1m'
        self.style['underline'] = '\033[4m'
    
    def _clear(self) -> None:
        self.air_time_counter = round(time.time() * 1000) # Set timestamp to now

        self.table.clear_rows()
        system('cls' if name == 'nt' else 'clear')
    
    def _get_airtime(self) -> str:
        date_obj = datetime.fromtimestamp(self.air_time_counter / 1000)
        date_str = date_obj.strftime('%H:%M:%S')
        return date_str
    
    def _format_previous_track(self, track: object) -> list:
        duration = track['timers']['segue_begin'] - \
            track['timers']['_track_begin']
        duration = str(timedelta(milliseconds=duration))[-12:][:-5]

        intro = str(timedelta(milliseconds=track['timers']['intro_end']))[-10:][:-5]

        try:
            color = self.color[track['_ui']['text_color']]
        except Exception as e:
            # print(e)
            color = self.color['gray']

        track_data = [
            color + 'PREVIOUS' + self.end_format,
            color + str(track['cut']) + self.end_format,
            color + track['category'] + self.end_format,
            color + track['meta']['title'] + self.end_format,
            color + track['meta']['artist'] + self.end_format,
            color + str(duration) + self.end_format,
            color + str(intro) + self.end_format
        ]

        return track_data

    def _format_current_track(self, track: object) -> list:
        duration_ms = track['timers']['segue_begin'] - \
            track['timers']['_track_begin']
        duration = str(timedelta(milliseconds=duration_ms))[-12:][:-5]

        intro = str(timedelta(milliseconds=track['timers']['intro_end']))[-10:][:-5]

        track_data = [
            self.color['gray'] + self.bg['red'] + self.style['bold'] +  '>ON AIR<',
            track['cut'],
            track['category'],
            track['meta']['title'],
            track['meta']['artist'],
            duration,
            intro + self.end_format
        ]
        
        self.air_time_counter += duration_ms

        return track_data
    
    def _format_upcoming_track(self, track: object, i: int) -> list:
        duration_ms = track['timers']['segue_begin'] - \
            track['timers']['_track_begin']
        duration = str(timedelta(milliseconds=duration_ms))[-12:][:-5]

        intro = str(timedelta(milliseconds=track['timers']['intro_end']))[-10:][:-5]

        air_time = self._get_airtime()

        try:
            color = self.color[track['_ui']['text_color']]
        except Exception as e:
            color = self.color['gray']

        track_data = [
            color + air_time + self.end_format,
            color + str(track['cut']) + self.end_format,
            color + track['category'] + self.end_format,
            color + track['meta']['title'] + self.end_format,
            color + track['meta']['artist'] + self.end_format,
            color + str(duration) + self.end_format,
            color + str(intro) + self.end_format
        ]

        self.air_time_counter += duration_ms

        return track_data

    def update(self, upcoming_tracks: list) -> None:
        '''Update playlist table.
        This table should consist of the previous track,
        currently airing track, and next `n` tracks to come.'''

        self._clear()

        for i, track in enumerate(upcoming_tracks):
            if i == 0: 
                self.table.add_row(self._format_previous_track(track))
            elif i == 1: 
                self.table.add_row(self._format_current_track(track))
            else:
                self.table.add_row(self._format_upcoming_track(track, i))
        
        print(self.table)


class AudioPlayer:
    def __init__(self, playlist_file: str, cuts_file: str):
        self.playlist_file = playlist_file
        self.cuts_file = cuts_file
        self.playlist_data = self.read_playlist()
        self.read_cuts()

    def update_pad(self, track: object) -> None:
        '''Write current program ancillary data struct to json file'''
        with open(PAD_OUT_FILE, 'w') as f:
            f.write(json.dumps(track, indent=2))
            
        if ENABLE_BA1_PAD:
            # Send program ancillary data to BreakawayOne audio processor
            pad_thread = threading.Thread(
                target=self._send_pad_http, args=(track,))
            pad_thread.daemon = True
            pad_thread.start()

    def _send_pad_http(self, track: object) -> None:
        url = f'http://{PAD_HOST}:{PAD_PORT}/parameter/{PAD_PROC}/strm/metadata_strm?set={track["meta"]["artist"]} - {track["meta"]["title"]}'
        try:
            r = requests.get(url, timeout=2)
        except:
            return

    def read_playlist(self) -> str:
        '''Read playlist file into array of cuts'''
        with open(self.playlist_file, 'r') as f:
            playlist = f.readlines()
        return playlist

    def read_cuts(self) -> None:
        '''Read cut json file into python objects'''
        with open(self.cuts_file, 'r') as f:
            self.cut_data = json.load(f)
            self.cuts = self.cut_data['cuts']

    def update_table(self, i: int) -> None:
        '''Update the TUI with new track data'''
        playlist_wrap_counter = 0
        track_data = []

        # Previous Track
        if i == 0: 
            '''The playlist loops forever, so if we're playing
            the first item of the playlist, the last item
            played will have been the last item in the playist
            '''
            track_data.append(self.playlist[len(self.playlist) - 1])
        else:
            track_data.append(self.playlist[i - 1])
        
        # Current Track
        track_data.append(self.playlist[i])

        for j in range (i + 1, i + NEXT_TRACKS_TO_DISPLAY + 1):

            if j >= len(self.playlist):
                track_data.append(self.playlist[playlist_wrap_counter])
                playlist_wrap_counter += 1
            else:
                track_data.append(self.playlist[j])

        table.update(track_data)

    def play_playlist(self) -> None:
        '''Play out the playlist described in self.playlist using cut data from self.cuts'''
        for i, track in enumerate(self.playlist):
            current_track = track['_links']['audio']

            self.play(current_track)

            self.update_table(i)
            self.update_pad(track)

            if track['topplay'] == False:
                sleep(track['timers']['segue_begin'] / 1000)

            # Need to check if last in array, and if yes loop around
            else:
                next_track = self.playlist[i+1]
                next_ramp = next_track['timers']['intro_end'] - \
                    next_track['timers']['intro_begin']

                if next_ramp < track['timers']['segue_begin']:
                    # TopPlay cut too long for next song ramp, so stall ramp by diff
                    sleep((track['timers']['segue_begin'] - next_ramp) / 1000)
                # else start immediately


    def play(self, current_track: str) -> None:
        playout_thread = threading.Thread(
                target=self._play, args=(current_track,))
        playout_thread.daemon = True
        playout_thread.start()


    def _play(self, track: str) -> None:
        '''Play a single cut from playlist'''
        try:
            playsound(track)
        except Exception as e:
            print('Unable to play track. Skipping...')


    def construct_playlist(self) -> None:
        '''Associate CUT ID in playlist file with all cut object data from self.cuts'''
        self.playlist = []
        for line in self.playlist_data:
            data = line.split(' ')

            cut = data[0].strip()
            try:
                # Not actually doing any of this yet
                eof_action = data[1].strip()
                timed_event = data[2].strip()
                timed_event_time = data[3].strip()
            except Exception as e:
                print(e)

            try:
                self.playlist.append(self.cuts[cut])
            except KeyError:
                print(f'Cut ID {cut} not in database. Skipping...')
                continue
            except Exception as e:
                print(e)
                continue

        if len(self.playlist) < NEXT_TRACKS_TO_DISPLAY -1:
            '''Until I fix wraparound issues with small playlist, error out'''
            exit(f'Error: Playlist must contain at least {NEXT_TRACKS_TO_DISPLAY} cuts to play.')


if __name__ == '__main__':
    table = PlaylistTable()

    player = AudioPlayer(PLAYLIST_FILE, CUTS_DB_FILE)

    player.construct_playlist()

    '''Loop playlist forever'''
    while 1:
        player.play_playlist()
