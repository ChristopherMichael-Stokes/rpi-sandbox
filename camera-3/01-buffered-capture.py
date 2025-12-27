# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = [
#     "loguru",
#     "numpy",
#     "opencv-contrib-python",
#     "tqdm",
#     "typer",
# ]
# ///
import threading
import time
from collections import deque

import cv2 as cv
import typer
from loguru import logger
from tqdm.auto import tqdm


class FrameBuffer(threading.Thread):
    def __init__(
        self,
        protocol: str,
        ip: str,
        port: str,
        interrupt: threading.Event,
        maxlen: int = 2,
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
        url = f"{self.address}/{params}"

        self.cap = cv.VideoCapture(url, apiPreference=cv.CAP_FFMPEG)
        self.cap.set(cv.CAP_PROP_BUFFERSIZE, 0)
        self.cap.set(cv.CAP_PROP_DTS_DELAY, 0)
        self.cap.set(cv.CAP_PROP_HW_ACCELERATION, cv.VIDEO_ACCELERATION_ANY)

        # Using deque as a LIFO queue
        self.buffer = deque(maxlen=maxlen)

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
        while (ret := self.cap.read())[0]:
            _, frame = ret
            self.buffer.append(frame)
            if self.interrupt.is_set():
                logger.info(f"Killing stream - {self.address}")
                self.buffer.clear()
                self.cap.release()
                break


def main(protocol: str = "tcp", ip: str = "192.168.1.254", port: str = "9998") -> None:
    interrupt = threading.Event()
    frame_buffer = FrameBuffer(protocol, ip, port, interrupt)
    frame_buffer.start()

    try:
        for frame in tqdm(frame_buffer):
            # ! real-time CV processing goes here.  The buffer means we'll always be running
            # ! on the most recently recieved frame so the iteration rate of this loop
            # ! is also the fps

            cv.imshow(frame_buffer.address, frame)
            if (
                cv.waitKey(1) == ord("q")
                or cv.getWindowProperty(frame_buffer.address, cv.WND_PROP_VISIBLE) < 1
            ):
                break
    finally:
        interrupt.set()
        frame_buffer.join()


if __name__ == "__main__":
    typer.run(main)
