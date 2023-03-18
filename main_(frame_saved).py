from PIL import Image, ImageSequence
import glob
import shutil
import os
import time

def magnification(image_size):
    magnify = int(400/max(image_size))
    if (magnify > 12):
        magnify = 12
    return magnify

def mov2dir(saved_file, dest_dir):
    target_path = f'./{dest_dir}'
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    shutil.move(saved_file, f'{target_path}/{saved_file}')

def major(img_name):
    frame_cnt = 0
    with Image.open(img_name) as img:
        mag_size = magnification(img.size)
        for frame in ImageSequence.Iterator(img):
            frame_delay_list.append(frame.info['duration'])
            frame = resizing(mag_size, frame)
            # frame_list.append(frame)
            delay4d = '{:04d}'.format(img.info['duration']) # temp
            framecnt3d = '{:03d}'.format(frame_cnt)
            name_frame = f'{img_name}_{framecnt3d}_{delay4d}.png'
            name_frame_list.append(name_frame)    
            frame.save(name_frame) #temp
            frame_cnt += 1

def resizing(mag, img_obj):
    img_obj = img_obj.resize(
        (img_obj.width * mag, img_obj.height * mag), resample=Image.NEAREST)
    # bg_img = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    bg_img = Image.new("RGBA", (400, 400), (255, 255, 255, 0))
    offset = ((bg_img.width - img_obj.width) // 2,
              (bg_img.height - img_obj.height) // 2)
    bg_img.paste(img_obj, offset)
    return bg_img


def asm(frames_name, delays, name_out):
    fm_opened = []
    for file in frames_name:
        fm_opened.append(Image.open(file))
    fm_opened[0].save(
        f'{name_out}.png',
        format='PNG',
        save_all=True,
        append_images=fm_opened[1:],
        duration=delays,
        disposal=1,
        loop=0)
    fm_opened.clear()

def del_residue(residue_li):
    for files in residue_li:
        os.remove(files)

# ---------------------------------------------------------------------#
frame_delay_list = []
name_frame_list = []

process_no = 0
t_start = time.time()
src_img_list = glob.glob('*.gif')

for name in src_img_list:
    pure_name = name.replace('.gif', '')
    major(name)
    asm(name_frame_list, frame_delay_list, pure_name)
    mov2dir(f'{pure_name}.png','enlarged_apng')
    frame_delay_list.clear()
    del_residue(name_frame_list)
    name_frame_list.clear()
    process_no += 1
    if(process_no == len(src_img_list)):
        print(f"{process_no}/{len(src_img_list)} done.")
    else:
        print(f"{process_no}/{len(src_img_list)} done.", end="\r")
    # time.sleep(0.5)
        
    
t_end = time.time()
print(f"Task Done in {round(t_end-t_start,2)}s.")
