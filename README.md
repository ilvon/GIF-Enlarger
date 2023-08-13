# Animated GIF (Pixel Art) Enlarger
![VERSION](https://img.shields.io/badge/v1.0.2-0047AB)
![PYTHON](https://img.shields.io/badge/Python-3.11.2-green)
![PILLOW](https://img.shields.io/badge/Pillow-9.4.0-green)
![CPP_MAGICK](https://img.shields.io/badge/Magick++-7.1.1.13--1-violet)

A simple python script for enlarging animated GIF (pixel art) and convert it into an APNG *(by default with [Nearest-Neighbor Interpolation](https://en.wikipedia.org/wiki/Nearest-neighbor_interpolation)*).

Tested under Python 3.11.2 & Pillow 9.4.0.

## Usage
- Download the python script **main.py**  
- Download the executable (built by PyInstaller) from [Release](https://github.com/thisObedience/GIF-Enlarger/releases)

## Option
|         Args         |                                  Description                                  |
|:--------------------:|:-----------------------------------------------------------------------------:|
| `-d` , `--dimension` | Dimension of the output (square) apng (Default=400px, Min.=Source image size) |
|   `-l` , `--limit`   |         Limit for the maximum magnification (Default=12, No limit=0)          |
|   `-n`, `--online`   |                     Using online image with URL as source                     |
|   `-i`, `--input`    |                       Image input format (Default: `gif`)                       |
|   `-o`, `--output`   |                      Image output format (Default: `png`)                       |
|  `-r`, `--resample`  |                Type of image interpolation (Default = NEAREST)                | 

### Options for Resampling Filters

**Details**: [Pillow Documentation](https://pillow.readthedocs.io/en/stable/handbook/concepts.html#filters)

| `-r` Values | Filter Name |
|:------:|:-----------:|
|  `0`   |   NEAREST   |
|  `1`   |     BOX     |
|  `2`   |  BILINEAR   |
|  `3`   |   HAMMING   |
|  `4`   |   BICUBIC   |
|  `5`   |   LANCZOS   |



## Remarks
1. By default, the output file format will be `.png` with resolution = 400 × 400
2. The output file will placed into a subfolder 'enlarged_apng'
3. Pillow is required
