#!/bin/env python3
from time import sleep
import os
import threading

'''
THE WHOLE PULSEMEETER API IS STUPID UNRELIABLE SO I AM
ABANDONING ITS USE IN FAVOR OF THE JACK2 SYSTEM. WHICH
IS...ANNOYING BUT COMES WITH THE FUNCTIONALITY NEEDED.
'''

class Channel:
    def __init__(self, id: str):
        self.id = id
        self.volume = self.get_volume()
        self.mute = self.get_mute()
        #self.name = self.get_name()

    def get_volume(self) -> int | None:
        try:
            return int(os.system(f'pulsemeeter get volume {self.id}'))
        except Exception as e:
            print(e)
        return None

    def get_mute(self) -> bool | None:
        try:
            return bool(os.system(f'pulsemeeter get mute {self.id}'))
        except Exception as e:
            print(e)
        return None

    def get_name(self) -> str | None:
        try:
            return os.system(f'pulsemeeter get name {self.id}')
        except Exception as e:
            print(e)
        return None

    def set_volume(self, volume: int) -> None:
        wt = threading.Thread(target=self._set_volume_sync, args=(volume,))
        wt.start()

    def _set_volume_sync(self, volume: int) -> None:
        os.system(f'pulsemeeter volume {self.id} {volume}')


class PulseMeeter:
    def __init__(self):
        self.vi1 = Channel('vi1')
        self.vi2 = Channel('vi2')
        self.vi3 = Channel('vi3')
        self.a1 = Channel('a1')
        self.a2 = Channel('a2')
        self.a3 = Channel('a3')
        self.b1 = Channel('b1')
        self.b2 = Channel('b2')
        self.b3 = Channel('b3')

    def fade_in(self, channel: Channel, duration: int) -> None:
        level = 0
        step_time = duration / 100

        while level < 100:
            level += 1
            channel.set_volume(level)
            sleep(step_time / 1000)

    def fade_out(self, channel: Channel, duration: int) -> None:
        level = 100
        step_time = duration / 100

        while level > 0:
            level -= 1
            channel._set_volume_sync(level)
            sleep(step_time / 1000)




if __name__ == '__main__':
    pm = PulseMeeter()
    pm.fade_out(pm.a1, 2000)
    pm.fade_out(pm.a2, 1000)
    pm.fade_in(pm.a1, 1000)
    pm.fade_in(pm.a2, 2000)
