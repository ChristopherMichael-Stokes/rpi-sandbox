# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = [
#     "numpy",
#     "opencv-contrib-python",
#     "typer",
# ]
# ///
import cv2 as cv
import typer


def main(protocol: str = "tcp", ip: str = "192.168.1.254", port: str = "9998") -> None:
    url = f"{protocol}://{ip}:{port}"
    params = "?" + "&".join(
        [
            "fflags=nobuffer",
            "flags=low_delay",
            "framedrop",
            "probesize=32",
            "sync=ext",
        ]
    )
    url = f"{url}/{params}"

    cap = cv.VideoCapture(url, apiPreference=cv.CAP_FFMPEG)
    cap.set(cv.CAP_PROP_BUFFERSIZE, 0)
    cap.set(cv.CAP_PROP_DTS_DELAY, 0)
    cap.set(cv.CAP_PROP_HW_ACCELERATION, cv.VIDEO_ACCELERATION_ANY)

    try:
        while (ret := cap.read())[0]:
            cv.imshow(url, ret[1])
            if cv.waitKey(1) == ord("q"):
                break
    finally:
        cap.release()
        cv.destroyAllWindows()


if __name__ == "__main__":
    typer.run(main)
