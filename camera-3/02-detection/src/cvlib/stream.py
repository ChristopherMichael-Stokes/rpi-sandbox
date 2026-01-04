import threading
import time
from collections import deque

import cv2 as cv
from loguru import logger


class FrameBuffer(threading.Thread):
    def __init__(
        self,
        protocol: str,
        ip: str,
        port: str,
        interrupt: threading.Event,
        maxlen: int = 200,
    ) -> None:
        super().__init__()
        self.interrupt = interrupt
        self.address = f"{protocol}://{ip}:{port}"
        params = "?" + "&".join(
            [
                "fflags=nobuffer",
                "flags=low_delay",
                "framedrop",
                "probesize=32",
                "sync=ext",
            ]
        )
        self.url = f"{self.address}/{params}"

        # Using deque as a LIFO queue
        self.buffer = deque(maxlen=maxlen)

    def init_cap(self) -> None:
        self.cap = cv.VideoCapture(self.url, apiPreference=cv.CAP_FFMPEG)
        self.cap.set(cv.CAP_PROP_BUFFERSIZE, 0)
        self.cap.set(cv.CAP_PROP_DTS_DELAY, 0)
        self.cap.set(cv.CAP_PROP_HW_ACCELERATION, cv.VIDEO_ACCELERATION_ANY)

    def __iter__(self):
        logger.info(f"Waiting for stream - {self.address}")
        while not self.is_alive():
            time.sleep(0.1)

        logger.info(f"Starting buffered iteration - {self.address}")
        while not self.interrupt.is_set():
            while not self.buffer:
                time.sleep(0.001)
                if self.interrupt.is_set():
                    return

            yield self.buffer.pop()

    def run(self):
        self.init_cap()
        while (ret := self.cap.read())[0]:
            _, frame = ret

            self.buffer.append(frame)
            if self.interrupt.is_set():
                logger.info(f"Killing stream - {self.address}")
                self.buffer.clear()
                self.cap.release()
                break
