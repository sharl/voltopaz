# -*- coding: utf-8 -*-
from dataclasses import dataclass

from PIL import Image
from icoextract import IconExtractor
from pycaw.pycaw import AudioUtilities
import comtypes


@dataclass
class Info:
    name: str
    path: str
    icon: Image
    volume: float


def get_info() -> list[Info]:
    info = []

    comtypes.CoInitialize()
    try:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            process = session.Process
            if process:
                volume = session.SimpleAudioVolume
                app_path = process.exe()
                info.append(
                    Info(
                        name=process.name(),
                        path=app_path,
                        icon=Image.open(IconExtractor(app_path).get_icon()),
                        volume=volume.GetMasterVolume(),
                    )
                )

        # 参照をループ毎に確実に消す
        if 'process' in locals():
            del process
        if 'session' in locals():
            del session
        if 'volume' in locals():
            del volume
        if 'app_path' in locals():
            del app_path
        if 'sessions' in locals():
            del sessions

    finally:
        comtypes.CoUninitialize()

    return info
