#!/usr/bin/env python3

from pydub import AudioSegment


class Transcode:
    def __init__(self, audio_directory: str, normalize: bool = True):

        self.audio_directory = audio_directory
        self.normalize_on_import = normalize
        self.audio_format = 'wav'
        self.proxy_cuts_enabled = True
        self.proxy_format = 'mp3'
        self.proxy_bitrate = '96k'

    def create_wav(self, segment: AudioSegment, out_file: str) -> bool:
        '''Create a WAV file from pydub.AudioSegment'''
        try:
            segment.export(out_file, format=self.audio_format)
            return True
        except Exception as e:
            return False

    def create_proxy(self, segment: AudioSegment, out_file: str) -> bool:
        '''Create a low bitrate mp3 proxy file from pydub.AudioSegment'''
        try:
            segment.export(out_file, format=self.proxy_format,
                           bitrate=self.proxy_bitrate)
            return True
        except Exception as e:
            print(e)
            return False

    def import_cut(self, import_file_path: str, cut_id: int | str):
        '''Handle importing new audio into AZPlayer'''
        try:
            segment = AudioSegment.from_file(import_file_path)
        except Exception as e:
            print(e)
            return

        if self.normalize_on_import:
            segment = segment.normalize()

        if self.proxy_cuts_enabled:
            proxy_out_file = f'{self.audio_directory}/{cut_id}.{self.proxy_format}'
            proxy_ok = self.create_proxy(segment, proxy_out_file)
        else:  # If no proxy, just set ok as True to avoid downstream trouble logic
            proxy_ok = True

        wav_out_file = f'{self.audio_directory}/{cut_id}.{self.audio_format}'
        wav_ok = self.create_wav(segment, wav_out_file)

        return (wav_ok, proxy_ok)
