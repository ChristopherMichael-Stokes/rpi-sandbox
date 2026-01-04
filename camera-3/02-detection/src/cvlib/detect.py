import threading
from typing import Literal

import cv2 as cv
import numpy as np
import rfdetr
import supervision as sv
import torch
import typer
from tqdm.auto import tqdm

from .stream import FrameBuffer

app = typer.Typer()

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


@app.command()
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


if __name__ == "__main__":
    app()
