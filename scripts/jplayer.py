#!/usr/bin/env python3

"""Play a sound file.

This only reads a certain number of blocks at a time into memory,
therefore it can handle very long files and also files with many
channels.

NumPy and the soundfile module (http://PySoundFile.rtfd.io/) must be
installed for this to work.

"""
# import argparse
import queue
import sys
import threading

import jack
import soundfile as sf

import time  # @TODO REMOVE DEV ONLY

# parser = argparse.ArgumentParser(description=__doc__)

# parser.add_argument('filename', help='audio file to be played back')
# parser.add_argument(
#     '-b', '--buffersize', type=int, default=20,
#     help='number of blocks used for buffering (default: %(default)s)')
# parser.add_argument('-c', '--clientname', default='AZPlayer',
#                     help='JACK client name')
# parser.add_argument('-m', '--manual', action='store_true',
#                     help="don't connect to output ports automatically")

# args = parser.parse_args()

# if args.buffersize < 1:
#     parser.error('buffersize must be at least 1')


class JackPlayer:
    def __init__(self, buffersize: int = 20, clientname: str = '(undef)'):
        self.client_name = clientname

        self.output_width = 2
        self.dtype = 'float32'
        self.autopatch_output = True

        self.buffersize = buffersize
        self.q = queue.Queue(maxsize=self.buffersize)
        self.event = threading.Event()

        self.client = jack.Client(self.client_name)
        self.blocksize = self.client.blocksize
        self.samplerate = self.client.samplerate
        self.client.set_xrun_callback(self.xrun)
        self.client.set_shutdown_callback(self.shutdown)
        self.client.set_process_callback(self.process)

        self.init_output_channel(width=self.output_width)

    def print_error(self, *args):
        print(*args, file=sys.stderr)

    def xrun(self, delay):
        print(f'XRun occurred. Increase JACK period size? delay={delay}')

    def shutdown(self, status, reason):
        self.print_error('JACK shutdown!')
        self.print_error('status:', status)
        self.print_error('reason:', reason)
        self.event.set()

    def stop_callback(self, msg: str = ''):
        if msg:
            self.print_error(msg)

        for port in self.client.outports:
            port.get_array().fill(0)

        self.event.set()
        raise jack.CallbackExit

    def process(self, frames):
        if frames != self.blocksize:
            self.stop_callback(
                'Blocksize has changed. That should not happen.')
        try:
            data = self.q.get_nowait()
        except queue.Empty:
            self.stop_callback('Buffer Underrun. Increase buffer size?')

        if data is None:
            self.stop_callback()  # Playback finished

        for channel, port in zip(data.T, self.client.outports):
            port.get_array()[:] = channel

    def init_output_channel(self, width: int = 2):
        for ch in range(1, width+1):
            self.client.outports.register(f'AZPlayer Out {ch}')

    def play(self, filename: str):
        try:
            with sf.SoundFile(filename) as f:
                block_generator = f.blocks(
                    blocksize=self.blocksize, dtype=self.dtype, always_2d=True, fill_value=0)

                for _, data in zip(range(self.buffersize), block_generator):
                    self.q.put_nowait(data)  # Prefill queueueueueue

                with self.client:
                    if self.autopatch_output:
                        target_ports = self.client.get_ports(
                            is_physical=True, is_input=True, is_audio=True)

                        if len(self.client.outports) == 1 and len(target_ports) > 1:
                            # Mono file to multichannel audio device, so make dual mono from JackPlayer
                            self.client.outports[0].connect(target_ports[0])
                            self.client.outports[0].connect(target_ports[1])
                        else:  # 1:1 auto-mapping of channels
                            for source, target in zip(self.client.outports, target_ports):
                                source.connect(target)

                    timeout = self.blocksize * self.buffersize / self.samplerate

                    for data in block_generator:
                        self.q.put(data, timeout=timeout)

                    self.q.put(None, timeout=timeout)  # Signal end of file

                    self.event.wait()

        except KeyboardInterrupt:
            # parser.exit('\nInterrupted by user')
            exit(1)

        except (queue.Full):
            # A timeout occured, i.e. there was an error in the callback
            #parser.exit(1)
            exit(1)

        except Exception as e:
            #parser.exit(type(e).__name__ + ': ' + str(e))
            exit(type(e).__name__ + ': ' + str(e))


if __name__ == '__main__':
    player = JackPlayer(buffersize=20, clientname='4Play 1')
    time.sleep(2)
    player.play('./100001.wav')
