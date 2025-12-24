# Project 1, basic networked video streaming

Mostly follows the raspi camera software guide, with tweaks where possible to improve performance / workability.

## 1. Basic UDP stream

Starting the stream on the server (pi).  Low latency does actually have noticable latency improvments surprisingly, I thought the diff would be imperceptible.

```sh
rpicam-vid -t 0 -n --inline --low-latency --codec libav --libav-format mpegts -o udp://<local_ip_of_pc>:5000
```

Previewing frames from the client (pc) as per [this](https://superuser.com/a/1777079), cutting down buffers to minimum and allowing dropped frames (essential for UDP)

```sh
ffplay -probesize 32 -fflags nobuffer -flags low_delay -analyzeduration 1 -strict experimental -framedrop -f mpegts -vf setpts=0 udp://chris-pi.local:5000
```

Keeping a consistent stream that restarts after client disconnections:
```sh
while :; do rpicam-vid --camera 1 -t 0 -n --inline --listen --vflip 1 --low-latency --framerate 120 --width 1536 --height 864 -o tcp://0.0.0.0:9998 || true; done
```

Loading frames in a python process to memory ([opencv VideoCapture api](https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html#a57c0e81e83e60f36c83027dc2a188e80)): [01-capture.py](./01-capture.py)

Loading frames in a buffer and concurrently pulling the latest (threading, frame queue)
<!-- TODO: code -->

Loading frames directly from camera in a python process on the pi (lowest overhead possible, avoiding networking stack etc)
<!-- TODO: code -->

Loading frames in a cpp process to memory (translate python to cpp, api is very similar)
<!-- TODO: code -->

Inspecting and optimising network usage + bandwitdth (things like checking latency, protocol choice, bitrate, packet inspection etc)
<!-- TODO md file -->

## 2. <!-- TODO: other protocols -->
