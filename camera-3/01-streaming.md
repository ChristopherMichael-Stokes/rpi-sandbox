# Project 1, basic networked video streaming

Mostly follows the raspi camera software guide, with tweaks where possible to improve performance / workability.

## 1. Basic direct TCP / UDP stream

Starting the stream on the server (pi) with a basic protocol means that only a single client can read the stream at a time, and when the client connection dies so does the server.  TCP will mean that all packets will be retransmitted until the client accepts them potentially at the cost of latency while UDP does not not.  

The rpi `--low-latency` flag does actually have visually noticable latency improvments surprisingly, I thought the result would be imperceptible.

UDP stream from rpi camera:

```sh
rpicam-vid -t 0 -n --inline --low-latency --codec libav --libav-format mpegts -o udp://<local_ip_of_pc>:5000
```

Previewing frames from the client (pc) as per [this](https://superuser.com/a/1777079), cutting down buffers to minimum and allowing dropped frames (essential for UDP)

```sh
ffplay -probesize 32 -fflags nobuffer -flags low_delay -analyzeduration 1 -strict experimental -framedrop -f mpegts -vf setpts=0 udp://chris-pi.local:5000
```

Keeping a consistent TCP stream that restarts after client disconnections:

```sh
while :; do rpicam-vid --camera 1 -t 0 -n --inline --listen --vflip 1 --low-latency --framerate 120 --width 1536 --height 864 -o tcp://0.0.0.0:9998;  [ $? -eq 0 ] && break; done
```

TCP stream of a usb camera:

```sh
ffmpeg -f v4l2 -input_format mjpeg -framerate 30 -video_size 1920x1080 -i /dev/video16 -c:v libx264 -preset ultrafast -tune zerolatency -g 30 -flush_packets 1 -f mpegts tcp://0.0.0.0:9998?listen=1
```

Picking up the stream on the network:

```sh
ffplay -fflags nobuffer -flags low_delay -framedrop tcp://<rpi local ip>:1234
```

Loading frames in a python process to memory ([opencv VideoCapture api](https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html#a57c0e81e83e60f36c83027dc2a188e80)): [01-capture.py](./01-capture.py)

Loading frames in a buffer and concurrently pulling the latest (threading, frame queue) [01-buffered-capture.py](./01-buffered-capture.py)

Loading frames directly from camera in a python process on the pi (lowest overhead possible, avoiding networking stack etc), https://stackoverflow.com/questions/35166111/opencv-python-reading-video-from-named-pipe
<!-- TODO: code -->

Loading frames in a cpp process to memory (translate python to cpp, api is very similar)
<!-- TODO: code -->

Inspecting and optimising network usage + bandwitdth (things like checking latency, protocol choice, bitrate, packet inspection etc)
<!-- TODO md file -->

## 2. <!-- TODO: other protocols -->
