import argparse
import datetime
import json
import os

import cv2
import numpy as np
import pyrealsense2 as rs

#> parse input data
def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default='', help="images save path")
    parser.add_argument("--mode", type=int, default=0, help="0(auto) or 1(manual)")
    parser.add_argument("--data", type=int, default=0, help="0(RGB and depth, both are aligned), 1(RGB+stereo)")
    parser.add_argument("--image_format", type=int, default=0, help="option: 0->jpg 1->png")
    parser.add_argument("--image_width", type=int, default=1280, help="width of the image, recommended 1280 or 640")
    parser.add_argument("--image_height", type=int, default=720, help="height of the image, recommended 720 or 480")
    parser.add_argument("--fps", type=int, default=30, help="frame rate of shooting")
    opt = parser.parse_args()
    return opt

#> Align RGB images and depth images
def get_aligned_images(profile, dirname, aligned_frames, depth_scale):
    
    aligned_depth_frame = aligned_frames.get_depth_frame()
    color_frame = aligned_frames.get_color_frame()
    intr = color_frame.profile.as_video_stream_profile().intrinsics
    camera_parameters = {'fx': intr.fx, 'fy': intr.fy,
                         'ppx': intr.ppx, 'ppy': intr.ppy,
                         'height': intr.height, 'width': intr.width,
                         'depth_scale': profile.get_device().first_depth_sensor().get_depth_scale()
                         }
    with open(os.path.join(dirname, 'intrinsics.json'), 'w') as fp:
        json.dump(camera_parameters, fp)
    color_image = np.asanyarray(color_frame.get_data(), dtype=np.uint8)
    depth_image = np.asanyarray(aligned_depth_frame.get_data(), dtype=np.float32)
    mi_d = np.min(depth_image[depth_image > 0])
    ma_d = np.max(depth_image)
    depth = (255 * (depth_image - mi_d) / (ma_d - mi_d + 1e-8)).astype(np.uint8)
    depth_image_color = cv2.applyColorMap(depth, cv2.COLORMAP_JET)
    depth_image = np.asanyarray(aligned_depth_frame.get_data(), dtype=np.float32) * depth_scale * 1000
    return color_image, depth_image, depth_image_color

def stream_RGB_Depth_aligned_data(opt, dirname, dir_list):
    pipeline = rs.pipeline()
    config = rs.config()    
    config.enable_stream(rs.stream.depth, opt.image_width, opt.image_height, rs.format.z16, opt.fps)
    config.enable_stream(rs.stream.color, opt.image_width, opt.image_height, rs.format.bgr8, opt.fps)
    profile = pipeline.start(config)
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    align_to = rs.stream.color
    align = rs.align(align_to)
    flag = 0
    n = 0
    print("Start streaming RGB images ...")
    while True:
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        try:  
            rgb, depth, depth_rgb = get_aligned_images(profile, dirname, aligned_frames, depth_scale)
            cv2.imshow('RGB image', rgb)
            key = cv2.waitKey(1)
            to_break, ret_flag, ret_n = control_data_flow(pipeline, opt, dir_list, key, flag, n, rgb, depth, depth_rgb, True)
            flag = ret_flag
            n = ret_n
            if to_break is True:
            	break
        except:
            pass

def stream_RGB_stereo_data(opt, dirname, dir_list):
    pipeline = rs.pipeline()
    config = rs.config() 

    config.enable_stream(rs.stream.color, opt.image_width, opt.image_height, rs.format.bgr8, opt.fps)   
    config.enable_stream(rs.stream.infrared, 1, opt.image_width, opt.image_height, rs.format.y8, opt.fps)
    config.enable_stream(rs.stream.infrared, 2, opt.image_width, opt.image_height, rs.format.y8, opt.fps)
    profile = pipeline.start(config)
    
    #> For stereo cameras we need to turn off the emitter to get grey-scale images
    device = profile.get_device()
    depth_sensor = device.query_sensors()[0]
    depth_sensor.set_option(rs.option.emitter_enabled, 0)
    
    flag = 0
    n = 0
    print("Start streaming RGB and stereo images ...")
    while True:
        frames = pipeline.wait_for_frames()
        try:  
            nir_left_frame = frames.get_infrared_frame(1)
            nir_right_frame = frames.get_infrared_frame(2)
            color_frame = frames.get_color_frame()
            #print("Here?")

            nir_left_image = np.asanyarray(nir_left_frame.get_data())
            nir_right_image = np.asanyarray(nir_right_frame.get_data())
            rgb_img = np.asanyarray(color_frame.get_data())
            
            left_img = np.frombuffer(nir_left_image, dtype=np.uint8).reshape((opt.image_height, opt.image_width))
            right_img = np.frombuffer(nir_right_image, dtype=np.uint8).reshape((opt.image_height, opt.image_width))
            
            rgb_stereo_image = np.hstack((left_img, right_img))
            
            cv2.imshow('RGB and stereo image', rgb_stereo_image)
            key = cv2.waitKey(1)
            to_break, ret_flag, ret_n = control_data_flow(pipeline, opt, dir_list, key, flag, n, rgb_img, left_img, right_img, False)
            flag = ret_flag
            n = ret_n
            if to_break is True:
            	break
        except:
            pass

def create_dirs(opt):
    now = datetime.datetime.now()
    if os.path.exists(os.path.join(opt.path, 'images')):
        dirname = opt.path
        if len(os.listdir(os.path.join(opt.path, 'images'))):
            li = sorted(os.listdir(os.path.join(opt.path, 'images')), key=lambda x: eval(x.split('.')[0]))
            n = eval(li[-1].split('.')[0])
        else:
            n = 0
    elif opt.path == '':
        n = 0
        dirname = os.path.join(opt.path, now.strftime("%Y_%m_%d_%H_%M_%S"))
    else:
        n = 0
        dirname = os.path.join(opt.path)
    color_dir = os.path.join(dirname, 'images')
    depth_dir = os.path.join(dirname, 'DepthImages')
    depth_color_dir = os.path.join(dirname, 'DepthColorImages')
    depth_npy_dir = os.path.join(dirname, 'DepthNpy')
    stereo_left_dir = os.path.join(dirname, 'images_left')
    stereo_right_dir = os.path.join(dirname, 'images_right')
    if not os.path.exists(dirname):
        os.mkdir(dirname)
        os.mkdir(color_dir)
        os.mkdir(depth_dir)
        os.mkdir(depth_color_dir)
        os.mkdir(depth_npy_dir)
        os.mkdir(stereo_left_dir)
        os.mkdir(stereo_right_dir)
    
    return dirname, color_dir, depth_dir, depth_color_dir, depth_npy_dir, stereo_left_dir, stereo_right_dir
    
def control_data_flow(pipeline, opt, dir_list, key, flag, n, img1, img2, img3, save_depth_npy: False):
    image_formats = ['.jpg', '.png']
    if key == ord('q') or key == ord('Q'):
        pipeline.stop()
        return True, 0, 0
    elif opt.mode:
        if key == ord('s') or key == ord('S'):
            n = n + 1
            if opt.data == 0:
            	#> [img1, img2, img3] = [rgb, depth, depth_rgb]
            	cv2.imwrite(os.path.join(dir_list[0], str(n) + image_formats[opt.image_format]), img1)
            	cv2.imwrite(os.path.join(dir_list[1], str(n) + image_formats[opt.image_format]), img2)
            	cv2.imwrite(os.path.join(dir_list[2], str(n) + image_formats[opt.image_format]), img3)
            	if save_depth_npy is True:
            		np.save(os.path.join(dir_list[3], str(n)), img2)
            elif opt.data == 1:
            	#> [img1, img2, img3] = [rgb, image_left, image_right]
            	cv2.imwrite(os.path.join(dir_list[0], str(n) + image_formats[opt.image_format]), img1)
            	cv2.imwrite(os.path.join(dir_list[1], str(n) + image_formats[opt.image_format]), img2)
            	cv2.imwrite(os.path.join(dir_list[2], str(n) + image_formats[opt.image_format]), img3)
            
            print('{}{} is saved!'.format(n, image_formats[opt.image_format]))
        return False, 0, n
    else:
        if key == ord('s') or key == ord('S'):
            return False, 1
        if key == ord('w') or key == ord('W'):
            return False, 0
        if flag:
            n = n + 1
            if opt.data == 0:
            	cv2.imwrite(os.path.join(dir_list[0], str(n) + image_formats[opt.image_format]), img1)
            	cv2.imwrite(os.path.join(dir_list[1], str(n) + image_formats[opt.image_format]), img2)
            	cv2.imwrite(os.path.join(dir_list[2], str(n) + image_formats[opt.image_format]), img3)
            	if save_depth_npy is True:
            		np.save(os.path.join(dir_list[3], str(n)), img2)
            elif opt.data == 1:
            	cv2.imwrite(os.path.join(dir_list[0], str(n) + image_formats[opt.image_format]), img1)
            	cv2.imwrite(os.path.join(dir_list[1], str(n) + image_formats[opt.image_format]), img2)
            	cv2.imwrite(os.path.join(dir_list[2], str(n) + image_formats[opt.image_format]), img3)
            
            print('{}{} is saved!'.format(n, image_formats[opt.image_format]))
            return False, 1, n


if __name__ == "__main__":
    opt = parse_opt()
    dirname, color_dir, depth_dir, depth_color_dir, depth_npy_dir, stereo_left_dir, stereo_right_dir = create_dirs(opt)
    
    if opt.data == 0:
    	dir_list = [color_dir, depth_dir, depth_color_dir, depth_npy_dir]
    	stream_RGB_Depth_aligned_data(opt, dirname, dir_list)
    elif opt.data == 1:
    	dir_list = [color_dir, stereo_left_dir, stereo_right_dir]
    	stream_RGB_stereo_data(opt, dirname, dir_list)
    
    
    
    
