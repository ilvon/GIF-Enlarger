# Animated GIF (Pixel Art) Enlarger
A simple python script for enlarging animated GIF (pixel art) and convert it into an APNG *(by default with [Nearest-Neighbor Interpolation](https://en.wikipedia.org/wiki/Nearest-neighbor_interpolation)*.

Tested under Python 3.11.2 & Pillow 9.4.0.

## Usage
- Download the python script **argsBatch_dl_main.py**  
- Download the executable (built by PyInstaller) from [Release](https://github.com/thisObedience/GIF-Enlarger/releases)

## Option
|         Args         |                             Description                              |
|:--------------------:|:--------------------------------------------------------------------:|
| `-d` , `--dimension` | Dimension of the output (square) apng (Default=400px, Min.=Source image size) |
|   `-l` , `--limit`   |     Limit for the maximum magnification (Default=12, No limit=0)     |
|   `-n`, `--online`   |                Using online image with URL as source                 | 

## Remarks
1. By default, the output file format will be `.png` with resolution = 400 × 400
2. The output file will placed into a subfolder 'enlarged_apng'
3. Pillow is required
