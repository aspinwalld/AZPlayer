#!/bin/env python3

from time import sleep
import json
from uuid import uuid4
import logging
from logformatter import CustomFormatter
import engine

DEBUG = False

PLAYLIST_FILE = './data/playlist.txt'
CUTS_DB_FILE = './data/cuts.json'
PAD_OUT_FILE = './pad.json'

WS_CLIENT_HOST = '127.0.0.1'
WS_CLIENT_PORT = 3420


log = logging.getLogger(__name__)

if DEBUG:
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.INFO)

stdout_log = logging.StreamHandler()
stdout_log.setFormatter(CustomFormatter())
log.addHandler(stdout_log)


ape = engine.APE(log=log, ws_host=WS_CLIENT_HOST, ws_port=WS_CLIENT_PORT)


class AudioPlaylist:
    def __init__(self, playlist_file: str, cuts_file: str):
        self.playlist_file = playlist_file
        self.cuts_file = cuts_file
        self.playlist_data = self.read_playlist()
        self.read_cuts()

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

    def play_playlist(self) -> None:
        '''Play out the playlist described in self.playlist using cut data from self.cuts'''
        for i, track in enumerate(self.playlist):
            # current_track = track['_links']['audio']

            self.play(track)

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

    def play(self, track: str) -> None:
        ape.play(cut=track, output_device=None)

    def construct_playlist(self) -> None:
        '''Associate CUT ID in playlist file with all cut object data from self.cuts'''
        self.playlist = []

        i = 0 # Playlist track index

        for line in self.playlist_data:
            data = line.split(' ')

            cut = data[0].strip()
            try:
                eof_action = data[1].strip()
                # Not actually doing timed events yet
                timed_event = data[2].strip()
                timed_event_time = data[3].strip()
            except Exception as e:
                log.error(e)
                eof_action = 2 # Default to segue

            try:
                playlist_cut = self.cuts[cut]
                playlist_cut['playlist'] = {
                    'track_id': str(uuid4()),
                    'index': i,
                    'eof_code': eof_action
                }
                self.playlist.append(playlist_cut)

                i += 1

                log.info(f'Added cut {cut} to playlist.')

            except KeyError:
                log.error(f'Cut ID {cut} not in database. Skipping...')
                continue
            except Exception as e:
                log.error(e)
                continue


if __name__ == '__main__':

    playlist = AudioPlaylist(PLAYLIST_FILE, CUTS_DB_FILE)

    playlist.construct_playlist()

    '''Loop playlist forever'''
    while 1:
        playlist.play_playlist()
