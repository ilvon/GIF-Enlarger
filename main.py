from PIL import Image, ImageSequence
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from re import findall
from requests import get as req_get
from shutil import move as shutil_move
from time import time
from tqdm import tqdm
import argparse
import os
import sys


class gifEnlarger:
    class imageProcessing:
        def __init__(self, args, config, image_handler):
            self.args = args
            self.cfg_init = config
            self.FILE_HANDLER = image_handler
        
        def magnification(self, image_size):
            if self.args.dimension < max(image_size):
                magnify = 1
            else:
                magnify = int(self.args.dimension / max(image_size))
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
            
        def disasm(self, img_name, frame_list, frame_delay_list):
            frame_cnt = 0
            try:
                with Image.open(img_name) as img:
                    mag_size = self.magnification(img.size)
                    for frame in ImageSequence.Iterator(img):
                        if 'duration' in frame.info:
                            frame_delay = min(frame.info.get('duration', 0), 65535)
                        else:
                            frame_delay = 0

                        frame = self.resizing(mag_size, frame)
                        if self.args.output == 'gif':
                            frame = self.gif_palette_handler(frame)

                        frame_list.append(frame)
                        frame_delay_list.append(frame_delay)
                        frame_cnt += 1
            except FileNotFoundError:
                print(f'Unable to open "{img_name}". (Possible reason: File being deleted / Repeated downloads.)')
            except Exception as e:
                print(f"Error processing {img_name}: {e}")

            
        def resizing(self, mag, img_obj):
            img_obj = img_obj.resize(
                (img_obj.width * mag, img_obj.height * mag), resample=self.cfg_init['resampling'][self.args.resample])
            if max(img_obj.width, img_obj.height) > self.args.dimension:
                self.args.dimension = max(img_obj.width, img_obj.height)
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
        
        def image_processor(self, name):
            frame_list = []
            frame_delay_list = []
            try:
                pure_name = name.replace(f'.{self.args.input}', '')
                self.disasm(name, frame_list, frame_delay_list)

                if len(frame_list) and len(frame_delay_list):
                    output_img_name = self.asm(frame_list, frame_delay_list, pure_name)
                    self.FILE_HANDLER.mov2dir(output_img_name, f"{self.cfg_init['out_dir']}_{self.args.output}")
                else:
                    print(f"No frames to process for {name}, skipping.")

                if self.args.online:
                    try:
                        os.remove(name)
                    except FileNotFoundError:
                        pass
                    except Exception as e:
                        print(f"An error occurred while deleting {name}: {e}")
            except Exception as e:
                print(f"Error processing {name}: {e}")
    
    class fileHandler:
        def __init__(self, config: dict):
            self.cfg_init = config
        
        def img_download(self, request_content) -> list:
            urls = findall(r'https?://[^\s"]+', request_content)
            print(f'\n{len(urls)} images will be downloaded.\n')
            retrieved_images = []
            for img_url in urls:
                response = req_get(img_url)
                img_name = os.path.basename(img_url)
                if response.status_code == 200:
                    with open(img_name, 'wb') as f:
                        f.write(response.content)
                    retrieved_images.append(img_name)
            return retrieved_images
            
        def mov2dir(self, saved_file, dest_dir):
            target_path = f'./{dest_dir}'
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            resulting = f'{target_path}/{saved_file}'
            shutil_move(saved_file, resulting.replace('__new_tmp_imgs__', ''))
        
        def download_mode_move(self, dl_imgs):
            if not os.path.exists(f"./{self.cfg_init['download_dir']}"):
                os.makedirs(f"./{self.cfg_init['download_dir']}")
            for dls in dl_imgs:
                try:
                    shutil_move(dls, f"{self.cfg_init['download_dir']}/{dls}")
                except FileNotFoundError:
                    print(f'\n{dls} does not exist, unable to move to directory "downloads" (Possible reason: Repeated downloading from inserted URLs.)')

         
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
        self.parsed_args = self.args_defining()
        self.file_handler = self.fileHandler(self.cfg_init)
        self.processor = self.imageProcessing(self.parsed_args, self.cfg_init, self.file_handler)
        
    def args_defining(self):
        parser = argparse.ArgumentParser()
        ME_flags = parser.add_mutually_exclusive_group()
        parser.add_argument('-d', '--dimension', type=int, default=self.cfg_init['dimension'], metavar='',
                            help='Dimension of the output apng (Default=512px, Min.=Source image size)')
        parser.add_argument('-l', '--limit', type=int, default=self.cfg_init['mag'], metavar='',
                            help='Limit of the maximum magnification (Default=12, No limit=0)')
        ME_flags.add_argument('-n', '--online', default=False, action='store_true',
                            help='Using online image with URL as source')
        parser.add_argument('-i', '--input', type=str, default=self.cfg_init['in'], metavar='', choices=['png', 'gif', 'webp'],
                            help='Input images format (Default = gif)')
        parser.add_argument('-o', '--output', type=str, default=self.cfg_init['out'], metavar='', choices=['png', 'gif', 'webp'],
                            help='Output images format (Default = png)')
        parser.add_argument('-r', '--resample', type=int, default=0, metavar='',
                            help='Set the type of image interpolation (Default = NEAREST), Details: https://pillow.readthedocs.io/en/stable/handbook/concepts.html#filters')
        ME_flags.add_argument('-g', '--download', default=False, action='store_true',
                            help='Download the online images only (without anying enlargement)')
        return parser.parse_args()
        
    def gif_enlarger_main(self):
        self.args_defining()
        
        if self.parsed_args.online or self.parsed_args.download:
            print('URLs (Press Ctrl + Z on a new line to finish for Windows): ')
            content_urls = sys.stdin.read()
            downloaded_images = self.file_handler.img_download(content_urls)
            if self.parsed_args.download:
                self.file_handler.download_mode_move(downloaded_images)
                return

        t_start = time()
        src_img_list = glob(f'*.{self.parsed_args.input}') if not self.parsed_args.online else downloaded_images

        with ThreadPoolExecutor(max_workers=os.cpu_count()*2) as executor:
            list(tqdm(executor.map(self.processor.image_processor, src_img_list), desc="Processing Images", total=len(src_img_list), unit="img"))

        t_end = time()
        print(f"Task Done in {round(t_end-t_start, 2)}s.")


if __name__ == '__main__':
    try:
        enlarger = gifEnlarger()
        enlarger.gif_enlarger_main()
    except KeyboardInterrupt:
        print('\nProcess terminated.')
