# Camera 3

Projects in some way utilising the camera module version 3.  The projects will likely be more focused on usage and not go very deep on the module nor theory around digital capture.

## Resources

Computer vision theory

- [Computer Vision: Algorithms and Applications, 2nd ed.](https://szeliski.org/Book/)
- [Learning OpenCV 3](https://books.google.co.uk/books/about/Learning_OpenCV_3.html?id=LPm3DQAAQBAJ&redir_esc=y)

Libarary tutorials
- [opencv py](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html), [opencv c++](https://docs.opencv.org/4.x/d9/df8/tutorial_root.html)
- [gstreamer c](https://gstreamer.freedesktop.org/documentation/tutorials/index.html?gi-language=c)

Blogs & informal tutorials
- [Installing gstreamer and opencv on the pi 5](https://scientric.com/2024/09/24/opencv-and-gstreamer-on-the-raspberry-pi-5/)
- [Python gstreamer pipelines](https://brettviren.github.io/pygst-tutorial-org/pygst-tutorial.html)
- [rpicam-apps source](https://github.com/raspberrypi/rpicam-apps)

## Project ideas

1. Implementing and iterating upon a low latency networked video stream, starting with heavy reliance on out-of-the box functionality through rpicam libs followed by continuous latency refinement and profiling
2. Remote object detection making use of the stream implementation
3. Edge object detection on the pi itself, starting with real-time capable DL models and exploring classical approaches
