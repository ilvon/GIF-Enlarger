from re import findall
from requests import get as req_get
from os.path import exists as path_exists, basename as path_basename
from os import remove as os_remove, makedirs as os_makedirs
from PIL import Image, ImageSequence
from glob import glob
from shutil import move as shutil_move
from time import time
import argparse
import sys
from tqdm import tqdm


class gifEnlarger:
    class image_processing:
        def magnification(self, image_size):
            if self.args.dimension < max(image_size):
                    magnify = 1
            else:
                magnify = int(self.args.dimension/max(image_size))
            if self.args.limit:
                if magnify > self.args.limit:
                    magnify = self.args.limit
            return magnify
            
        def gif_palette_handler(self, frame):
            alpha_channel = frame.getchannel('A')
            frame_mask = Image.eval(alpha_channel, lambda a: 255 if a <= 128 else 0)
            frame = frame.convert('P').quantize(colors=256, dither=Image.NONE)
            frame.info['transparency'] = 0
            frame.paste(0, frame_mask)
            return frame
            
        def disasm(self, img_name):
            frame_cnt = 0
            try:
                with Image.open(img_name) as img:
                    mag_size = magnification(img.size)
                    for frame in ImageSequence.Iterator(img):
                        if 'duration' in frame.info:    #check for png's frame duration existence
                            if frame.info['duration'] <= 65535:
                                frame_delay_list.append(frame.info['duration'])
                            else:
                                frame_delay_list.append(65535)
                        else:
                            frame_delay_list.append(0)
                        frame = resizing(mag_size, frame)
                        if self.args.output == 'gif':
                            frame = gif_palette_handler(frame)
                        frame_list.append(frame)
                        frame_cnt += 1
            except FileNotFoundError:
                print(f'Unable to open \"{img_name}\". (Possible reason: File being deleted / Repeated downloads.)')

            
        def resizing(self, mag, img_obj):
            img_obj = img_obj.resize(
                (img_obj.width * mag, img_obj.height * mag), resample=cfg_init['resampling'][self.args.resample])
            if max(img_obj.width,img_obj.height) > self.args.dimension:
                self.args.dimension = max(img_obj.width,img_obj.height)
            bg_img = Image.new("RGBA", (self.args.dimension, self.args.dimension), (255, 255, 255, 0))
            offset = ((bg_img.width - img_obj.width) // 2,
                    (bg_img.height - img_obj.height) // 2)
            bg_img.paste(img_obj, offset)
            return bg_img
            
        def asm(self, frames, delays, name_out):
            if self.args.input == self.args.output:
                saving_filename = f'__new_tmp_imgs__{name_out}.{self.args.output}'
            else:
                saving_filename = f'{name_out}.{self.args.output}'
            disposal_type = 2 if self.args.output == 'gif' else 1
            frames[0].save(
                saving_filename,
                format=self.args.output,
                save_all=True,
                append_images=frames[1:],
                duration=delays,
                disposal=disposal_type,
                loop=0)
            return saving_filename
    
    class file_handling:
        def img_download(self, request_content) -> list:
            urls = findall(r'https?://[^\s"]+', request_content)
            print(f'\n{len(urls)} images will be downloaded.\n')
            retrieved_images = []
            for img_url in urls:
                response = req_get(img_url)
                img_name = path_basename(img_url)
                if response.status_code == 200:
                    with open(img_name, 'wb') as f:
                        f.write(response.content)
                    retrieved_images.append(img_name)
            return retrieved_images
            
        def mov2dir(self, saved_file, dest_dir):
            target_path = f'./{dest_dir}'
            if not path_exists(target_path):
                os_makedirs(target_path)
            resulting = f'{target_path}/{saved_file}'
            shutil_move(saved_file, resulting.replace('__new_tmp_imgs__', ''))
        
        def download_mode_move(self, dl_imgs):
            if not path_exists(f"./{cfg_init['download_dir']}"):
                os_makedirs(f"./{cfg_init['download_dir']}")
            for dls in dl_imgs:
                try:
                    shutil_move(dls, f"{cfg_init['download_dir']}/{dls}")
                except FileNotFoundError:
                    print(f'\n{dls} does not exist, unable to move to directory \"downloads\" (Possible reason: Repeated downloadings from inserted URLs.)')

        
    
    def __init__(self):
        self.cfg_init = {
            'dimension': 512,
            'mag': 12,
            'in': 'gif',
            'out': 'png',
            'out_dir': 'enlarged',
            'download_dir': 'downloads',
            'resampling': (Image.Resampling.NEAREST, Image.Resampling.BOX, 
                        Image.Resampling.BILINEAR, Image.Resampling.HAMMING, 
                        Image.Resampling.BICUBIC, Image.Resampling.LANCZOS)
        }
        self.args = self.args_defining()
        
    def args_defining(self):
        parser = argparse.ArgumentParser()
        ME_flags = parser.add_mutually_exclusive_group()
        parser.add_argument('-d', '--dimension', type=int, default=cfg_init['dimension'], metavar='',
                            help='Dimension of the output apng (Default=512px, Min.=Source image size)')
        parser.add_argument('-l', '--limit', type=int, default=cfg_init['mag'], metavar='',
                            help='Limit of the maximum magnification (Default=12, No limit=0)')
        ME_flags.add_argument('-n', '--online', default=False, action='store_true',
                            help='Using online image with URL as source')
        parser.add_argument('-i', '--input', type=str, default=cfg_init['in'], metavar='', choices=['png', 'gif', 'webp'],
                            help='Input images format (Default = gif)')
        parser.add_argument('-o', '--output', type=str, default=cfg_init['out'], metavar='', choices=['png', 'gif', 'webp'],
                            help='Output images format (Default = png)')
        parser.add_argument('-r', '--resample', type=int, default=0, metavar='',
                            help='Set the type of image interpolation (Default = NEAREST), Details: https://pillow.readthedocs.io/en/stable/handbook/concepts.html#filters')
        ME_flags.add_argument('-g', '--download', default=False, action='store_true',
                            help='Download the online images only (without anying enlargement)')
        return parser.parse_args()
        