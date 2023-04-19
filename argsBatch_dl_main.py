import re
import requests
import os
from PIL import Image, ImageSequence
import glob
import shutil
import time
import argparse

def args_defining():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dimension', type=int, default=400, metavar='',
                        help='Dimension of the output apng (Default=400px, Min.=Source image size)')
    parser.add_argument('-l', '--limit', type=int, default=12, metavar='',
                        help='Limit of the maximum magnification (Default=12, No limit=0)')
    parser.add_argument('-n', '--online', default=False, action='store_true', 
                        help='Using online image with URL as source')
    args = parser.parse_args()

def img_download(request_content):
    urls = re.findall(r'https?://[^\s"]+', request_content)
    for img_url in urls:
        response = requests.get(img_url)
        img_name = os.path.basename(img_url)
        if response.status_code == 200:
            with open(img_name, 'wb') as f:
                f.write(response.content)

def magnification(image_size):
    if args.dimension < max(image_size):
        magnify = 1
    else:
        magnify = int(args.dimension/max(image_size))
    if args.limit:
        if magnify > args.limit:
            magnify = args.limit
    return magnify

def mov2dir(saved_file, dest_dir):
    target_path = f'./{dest_dir}'
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    shutil.move(saved_file, f'{target_path}/{saved_file}')

def disasm(img_name):
    frame_cnt = 0
    with Image.open(img_name) as img:
        mag_size = magnification(img.size)
        for frame in ImageSequence.Iterator(img):
            if frame.info['duration'] <= 65535:
                frame_delay_list.append(frame.info['duration'])  
            else:
                frame_delay_list.append(65535)
            frame = resizing(mag_size, frame)
            frame_list.append(frame)
            frame_cnt += 1

def resizing(mag, img_obj):
    img_obj = img_obj.resize(
        (img_obj.width * mag, img_obj.height * mag), resample=Image.NEAREST)
    # bg_img = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
    if max(img_obj.width,img_obj.height) > args.dimension:
        args.dimension = max(img_obj.width,img_obj.height)
    bg_img = Image.new("RGBA", (args.dimension, args.dimension), (255, 255, 255, 0))
    offset = ((bg_img.width - img_obj.width) // 2,
              (bg_img.height - img_obj.height) // 2)
    bg_img.paste(img_obj, offset)
    return bg_img

def asm(frames, delays, name_out):
    frames[0].save(
        f'{name_out}.png',
        format='PNG',
        save_all=True,
        append_images=frames[1:],
        duration=delays,
        disposal=1,
        loop=0)
    
def gif_enlarger_main():
    global frame_delay_list, frame_list
    args_defining()
    frame_delay_list = []
    frame_list = []
    process_no = 0
    
    if args.online:
        contents = input('URL: ')
        img_download(contents)
        
    t_start = time.time()
    src_img_list = glob.glob('*.gif')
    for name in src_img_list:
        pure_name = name.replace('.gif', '')
        disasm(name)
        asm(frame_list, frame_delay_list, pure_name)
        mov2dir(f'{pure_name}.png', 'enlarged_apng')
        frame_delay_list.clear()
        frame_list.clear()
        process_no += 1
        if (process_no == len(src_img_list)):
            print(f"{process_no}/{len(src_img_list)} done.")
        else:
            print(f"{process_no}/{len(src_img_list)} done.", end="\r")
        if args.online:
            os.remove(name)
        
    t_end = time.time()
    print(f"Task Done in {round(t_end-t_start,2)}s.")
    
# ---------------------------------------------------------------------#

gif_enlarger_main()
