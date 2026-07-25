# -*- coding: utf-8 -*-
import ctypes
import queue
import threading

from PIL import Image
from pycaw.pycaw import AudioUtilities
from pystray import Icon, Menu, MenuItem
import comtypes
import darkdetect as dd

from get_info import get_info

APP_NAME = 'voltopaz'
PreferredAppMode = {
    'Light': 0,
    'Dark': 1,
}
# https://github.com/moses-palmer/pystray/issues/130
ctypes.windll['uxtheme.dll'][135](PreferredAppMode[dd.theme()])


class TaskTray:
    def __init__(self):
        self.stop_event = threading.Event()
        self.task_queue = queue.Queue()

        # app info {name: value}
        self.apps = {}
        # 今は決め打ち
        self.name = 'DQXGame.exe'
        self.min_vol = 20
        self.max_vol = 100
        # 最小状態を示す
        self.state = False

        self.min_image = None
        self.max_image = None
        self.set_icons(Image.open('icon.png'))

        self.app = Icon(name=APP_NAME, title=APP_NAME, icon=self.min_image)
        self.app.title = f'{self.name}'
        self.app.menu = Menu(self.build_menu)

    def set_icons(self, image: Image) -> None:
        # アイコン切り出し設定(中央を切り出す)
        ow, oh = (256, 256)
        cw, ch = (ow // 2, oh // 2)
        box = (
            (ow - cw) // 2,
            (oh - ch) // 2,
            (ow + cw) // 2,
            (oh + ch) // 2,
        )
        self.min_image = image.resize((ow, oh))
        self.max_image = image.resize((ow, oh)).crop(box)

    def build_menu(self):
        main_menu = [
            MenuItem(APP_NAME, self.doTask, visible=False, default=True),
        ]

        info = get_info()
        for item in info:
            self.apps[item.name] = item
            main_menu.append(
                MenuItem(item.name, self.set_target),
            )

        if len(info):
            main_menu.append(
                Menu.SEPARATOR,
            )
        main_menu.append(
            MenuItem('Exit', self.stopApp),
        )
        return main_menu

    def set_target(self, _, item):
        self.name = item.text
        self.set_icons(self.apps[item.text].icon)
        self.app.title = f'{self.name}'
        self.app.icon = self.min_image

    def com_worker(self):
        comtypes.CoInitialize()
        try:
            while not self.stop_event.is_set():
                try:
                    volume_level = self.task_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                sessions = AudioUtilities.GetAllSessions()
                for session in sessions:
                    if session.Process:
                        if session.Process.name().lower() == self.name.lower():
                            volume = session.SimpleAudioVolume
                            volume.SetMasterVolume(volume_level, None)
                            print(f'{self.name} volume: {volume_level}')

                # 参照をループ毎に確実に消す
                if 'session' in locals():
                    del session
                if 'volume' in locals():
                    del volume
                if 'sessions' in locals():
                    del sessions

        except Exception as e:
            print(f'com_worker exception {e}')

        finally:
            comtypes.CoUninitialize()

    def doTask(self):
        if self.state:
            self.task_queue.put(self.min_vol / 100)
            self.app.title = f'{self.name} {self.min_vol}'
            self.app.icon = self.min_image
        else:
            self.task_queue.put(self.max_vol / 100)
            self.app.title = f'{self.name} {self.max_vol}'
            self.app.icon = self.max_image

        self.state = not self.state

        self.app.menu = Menu(self.build_menu)
        self.app.update_menu()

    def stopApp(self, _, __):
        self.stop_event.set()
        self.app.stop()

    def runApp(self):
        self.stop_event.clear()

        threading.Thread(target=self.com_worker, daemon=True).start()

        self.app.run()


if __name__ == '__main__':
    TaskTray().runApp()
