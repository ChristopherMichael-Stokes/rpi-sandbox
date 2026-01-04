import threading
import time
from collections import deque
from typing import Literal

import cv2 as cv
import numpy as np
import rfdetr
import supervision as sv
import torch
import typer
from loguru import logger
from tqdm.auto import tqdm

ModelSize = Literal["large", "base", "nano"]
ModelDict: dict[ModelSize, type[rfdetr.detr.RFDETR]] = {
    "large": rfdetr.RFDETRLarge,
    "base": rfdetr.RFDETRBase,
    "nano": rfdetr.RFDETRNano,
}


def as_compiled[T: torch.nn.Module](model: T, dtype: torch.dtype | str) -> T:
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.backends.cudnn.deterministic = False

    model = model.to(dtype)
    model = torch.compile(model)  # type: ignore[invalid-assignment]
    return model


@torch.inference_mode()
def main(
    protocol: str = "tcp",
    ip: str = "192.168.1.254",
    port: str = "9998",
    model_size: ModelSize = "large",
) -> None:
    # Needs to fit evenly into 32 or 56 distinct dino patch tokens
    res = 544 if model_size == "nano" else 560
    model = ModelDict[model_size]()
    model.model.resolution = res
    # fp32 ~ 28fps
    # bf16 and fp16 ~ 33-35fps
    # compiled bf16 ~ 40 fps
    # + nano or base size ~ 50fps - hidden latency somewhere in the loop, need to debug where
    # ? intriguingly FPS correlates with stream resolution & framerate (server side) so potentially
    # ? there's a network bottleneck?

    model.model.model = as_compiled(model.model.model, torch.bfloat16)
    _ = model.predict(np.random.uniform(0, 1, (res, res, 3)))
    np.random.uniform
    id2label = model.class_names
    bounding_box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()
    print(model.model.model)
    print(f"Inference device: {model.model.device}")
    print(f"Inference resolution: {model.model.resolution}")
    print(f"Total params: {sum(p.numel() for p in model.model.model.parameters()):,}")

    interrupt = threading.Event()
    frame_buffer = FrameBuffer(protocol, ip, port, interrupt)
    frame_buffer.start()

    try:
        for frame in tqdm(frame_buffer):
            detections = model.predict(frame)

            if detections:
                labels = [id2label[id_] for id_ in detections.class_id]  # type: ignore
                annotated_image = bounding_box_annotator.annotate(
                    scene=frame, detections=detections
                )
                annotated_image = label_annotator.annotate(
                    scene=annotated_image, detections=detections, labels=labels
                )
                frame = np.array(annotated_image)

            cv.imshow(frame_buffer.address, frame)

            if (
                cv.waitKey(1) == ord("q")
                or cv.getWindowProperty(frame_buffer.address, cv.WND_PROP_VISIBLE) < 1
            ):
                break
    finally:
        interrupt.set()
        frame_buffer.join()


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


if __name__ == "__main__":
    typer.run(main)
