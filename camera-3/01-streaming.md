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

Loading frames in a python process to memory (read opencv tutorials, configure latency)
Loading frames in a cpp process to memory (read opencv tutorials, configure latency)
<!-- TODO: code -->

## 2. <!-- TODO: other protocols -->
