#!/bin/env python3

import wave
import time
import json
import threading
import pyaudio
import logging
from rws import WSClient
from logformatter import CustomFormatter
import asyncio

DEBUG = True
SERVICE_ID = 'azplay-ape'
WS_STARTUP_WAIT_MS = 2000
MIN_WS_MSG_INTERVAL_MS = 100


CUT_DATA = [
    {
        "playlist": {
            "track_id": "7f4ec6eb-cdec-4b00-a2d0-570e03eb7d35",
            "index": 0,
            "eod_code": 2
        },
        "category": "MUSIC",
        "cut": 100000,
        "duration": 60000,
        "meta": {
            "album": "",
            "artist": "Cantina Band",
            "title": "60 Second Song"
        },
        "timers": {
            "_track_begin": 0,
            "_track_end": 60000,
            "intro_begin": 0,
            "intro_end": 0,
            "segue_begin": 52000,
            "segue_end": 60000
        },
        "topplay": False,
        "_links": {
            "audio": "./audio/CantinaBand60.wav",
            "albumart": None
        },
        "_ui": {
            "text_color": "cyan"
        }
    },
    {
        "playlist": {
            "track_id": "7f4ec6eb-cdec-4b00-a2d0-570e03eb7d36",
            "index": 0,
            "eod_code": 2
        },
        "category": "MUSIC",
        "cut": 100000,
        "duration": 60000,
        "meta": {
            "album": "",
            "artist": "Cantina Band",
            "title": "60 Second Song"
        },
        "timers": {
            "_track_begin": 0,
            "_track_end": 60000,
            "intro_begin": 0,
            "intro_end": 0,
            "segue_begin": 52000,
            "segue_end": 60000
        },
        "topplay": False,
        "_links": {
            "audio": "./audio/CantinaBand60.wav",
            "albumart": None
        },
        "_ui": {
            "text_color": "cyan"
        }
    }
]


log = logging.getLogger(__name__)

if DEBUG:
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.INFO)

stdout_log = logging.StreamHandler()
stdout_log.setFormatter(CustomFormatter())
log.addHandler(stdout_log)


class APE:
    '''AZPlay APE (Audio Playout Engine)'''

    def __init__(self):
        # Instantiate PyAudio and initialize PortAudio system resources
        self.p = pyaudio.PyAudio()
        log.debug(f'Create pyAudio {self.p}')
        self.devices = self.get_devices()
        log.debug(
            f'Discovered {len(self.devices)} PortAudio devices: {self.devices}')
        self.playing = {}

        #self.ws = WSClient(log, url='ws://127.0.0.1:8080')
        self.ws = WSClient(log, host='127.0.0.1', port=8080)
        log.info('Starting websocket client...')
        # self.start_ws_client()
        self.ws.connect()
        log.info(
            f'Waiting {WS_STARTUP_WAIT_MS} ms for websocket connection...')
        time.sleep(WS_STARTUP_WAIT_MS / 1000)

    def start_ws_client(self):
        wst = threading.Thread(target=self._start_ws_client)
        wst.daemon = True
        wst.start()

    def _start_ws_client(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.ws.listen_forever())

    def get_devices(self) -> dict:
        '''Get {<id:int>: <name:str>} dict of PortAudio devices available to system'''
        devices = {}
        device_count = pyaudio.PyAudio.get_device_count(self.p)

        for i in range(0, device_count):
            device = pyaudio.PyAudio.get_device_info_by_index(self.p, i)
            devices[device['index']] = device['name']

        return devices

    def emit_message(self, msg_type: str, msg_data: object) -> None:
        '''Emit message via [tbd_messaging_service]'''
        msg_struct = {
            # milliseconds since unix epoch
            'timestamp': round(time.time() * 1000),
            'origin': SERVICE_ID,
            'message': msg_type,
            'data': msg_data
        }
        self.ws.send(msg_struct)

    def emit_track_start(self, cut_data: object, output_device: int) -> None:
        '''Emit track start message'''
        msg = {
            'playlist_track_id': cut_data['playlist']['track_id'],
            'cut_info': cut_data,
            'device': {
                'index': output_device,
                'name': None if output_device == None else self.devices[output_device]
            }
        }
        self.emit_message('stream.start', msg)

    def emit_track_update(self, cut_data: object, output_device: int, time_info: object, status: int) -> None:
        msg = {
            'playlist_track_id': cut_data['playlist']['track_id'],
            'buffer_latency': round((time_info['output_buffer_dac_time'] - time_info['current_time']) * 1000),
            'cut_id': cut_data['cut'],
            'device': {
                'index': output_device,
                'name': None if output_device == None else self.devices[output_device]
            },
            'status': status,
            'track_elapsed': round(time_info['input_buffer_adc_time'] * 1000)
        }
        self.emit_message('stream.update', msg)

    def play(self, cut: str, output_device: int | None = None) -> int:
        '''Spin up worker thread to handle single audio essence playout'''
        log.info(f'Starting player for cut {cut["cut"]}')
        p_thread = threading.Thread(
            target=self._play, args=(cut, output_device))
        p_thread.daemon = True
        p_thread.start()

    def _play(self, cut_data: object, output_device: int | None) -> int:
        '''Play audio in worker thread'''
        file_name = cut_data['_links']['audio']

        with wave.open(file_name, 'rb') as wf:
            track_id = cut_data['playlist']['track_id']
            self.playing[track_id] = cut_data
            self.playing[track_id]['last_track_update'] = round(
                time.time() * 1000)

            self.emit_track_start(cut_data, output_device)

            def callback(in_data, frame_count: dict, time_info: dict, status: int) -> tuple:
                '''Callback for playback'''
                data = wf.readframes(frame_count)

                now = round(time.time() * 1000)
                last_updated = self.playing[track_id]['last_track_update']

                if now - last_updated >= MIN_WS_MSG_INTERVAL_MS:
                    self.emit_track_update(
                        cut_data, output_device, time_info, status)
                    self.playing[track_id]['last_track_update'] = now
                # else skip emitting update

                return (data, pyaudio.paContinue)

            stream = self.p.open(format=self.p.get_format_from_width(wf.getsampwidth()),
                                 channels=wf.getnchannels(),
                                 rate=wf.getframerate(),
                                 output_device_index=output_device,
                                 output=True,
                                 stream_callback=callback)

            #self.playing[cut_data['cut']] = stream

            # Wait for stream to finish
            while stream.is_active():
                time.sleep(0.1)

            stream.close()
            try:
                self.playing.pop(track_id)
            except KeyError as e:
                log.error(
                    f'Error removing track_id {track_id} from playing struct.')
                log.debug(e)
            return 0


if __name__ == '__main__':
    ape = APE()
    ape.play(cut=CUT_DATA[0])
    time.sleep(52000/1000)
    ape.play(cut=CUT_DATA[1])
    time.sleep(72)

    ape.p.terminate()
