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

DEBUG = False
SERVICE_ID = 'azplay-ape'
WS_STARTUP_WAIT_MS = 2000
MIN_WS_MSG_INTERVAL_MS = 100


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

    def __init__(self, log, ws_host: str = '127.0.0.1', ws_port: int = 3420):
        # Instantiate PyAudio and initialize PortAudio system resources
        self.log = log

        self.p = pyaudio.PyAudio()
        log.debug(f'Create pyAudio {self.p}')
        self.devices = self.get_devices()
        log.debug(
            f'Discovered {len(self.devices)} PortAudio devices: {self.devices}')
        self.playing = {}

        # self.ws = WSClient(log, url='ws://127.0.0.1:8080')
        self.ws = WSClient(log, host=ws_host, port=ws_port)
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

    def emit_message(self, event: str, msg_data: object) -> None:
        '''Emit message via [tbd_messaging_service]'''
        msg_struct = {
            # milliseconds since unix epoch
            'timestamp': round(time.time() * 1000),
            'origin': SERVICE_ID,
            'event': event,
            'data': msg_data
        }
        try:
            self.ws.send(msg_struct)
        except Exception as e:
            log.error(e)

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

    def emit_track_end(self, cut_data: object, output_device: int) -> None:
        '''Emit track end message'''
        msg = {
            'playlist_track_id': cut_data['playlist']['track_id'],
            'cut_info': cut_data,
            'device': {
                'index': output_device,
                'name': None if output_device == None else self.devices[output_device]
            }
        }
        self.emit_message('stream.end', msg)

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
                                 output=True,  # Output Enable handled in mixer module
                                 stream_callback=callback)

            # self.playing[cut_data['cut']] = stream

            # Wait for stream to finish
            while stream.is_active():
                time.sleep(0.1)

            stream.close()
            self.emit_track_end(cut_data, output_device)
            try:
                self.playing.pop(track_id)
            except KeyError as e:
                log.error(
                    f'Error removing track_id {track_id} from playing struct.')
                log.debug(e)
            return 0
