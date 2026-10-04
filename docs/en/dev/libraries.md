# Software and libraries used

backingtrack's code is under the **MIT** license (see [LICENSE](https://github.com/wdog/backingtrack/blob/main/LICENSE)). It uses these programs and libraries, not
included in the repository:

| Software | Used for | License |
|---|---|---|
| [Python 3.8+](https://www.python.org) | the whole program | PSF License |
| [NumPy](https://numpy.org) | sampling engine, mix, reverb | BSD-3-Clause |
| [PyYAML](https://pyyaml.org) | reading and writing songs | MIT |
| [FFmpeg](https://ffmpeg.org) | amps and cabinets (convolution), EQ, compressors, limiter, MP3, FLAC, waveform | LGPL 2.1+ (GPL in some builds) |
| [GTK 4](https://www.gtk.org) | graphical interface | LGPL 2.1+ |
| [libadwaita](https://gnome.pages.gitlab.gnome.org/libadwaita/) | interface components | LGPL 2.1+ |
| [PyGObject](https://pygobject.gnome.org) | GTK from Python | LGPL 2.1+ |
| [Pillow](https://python-pillow.org) | only to generate logo and diagrams (`docs/make_images.py`) | MIT-CMU (HPND) |
| [SFZ](https://sfzformat.com) | open format for sampled instruments | open specification |
