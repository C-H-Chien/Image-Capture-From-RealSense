import pyrealsense2 as rs
import numpy as np
#from PIL import Image
import cv2

points = rs.points()
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.infrared, 1, 640, 480, rs.format.y8, 30)
config.enable_stream(rs.stream.infrared, 2, 640, 480, rs.format.y8, 30)
profile = pipeline.start(config)

def y8_to_grayscale(y8_data, width, height):
    """Converts Y8 data to a grayscale PIL Image."""
    # Create a numpy array from the Y8 data
    

    # Create a PIL Image from the numpy array
    img = Image.fromarray(y8_array, mode='L')
    return img

try:
    while True:
        frames = pipeline.wait_for_frames()
        nir_lf_frame = frames.get_infrared_frame(1)
        nir_rg_frame = frames.get_infrared_frame(2)
        if not nir_lf_frame or not nir_rg_frame:
            continue
        nir_lf_image = np.asanyarray(nir_lf_frame.get_data())
        nir_rg_image = np.asanyarray(nir_rg_frame.get_data())
        
        left_img = np.frombuffer(nir_lf_image, dtype=np.uint8).reshape((480, 640))
        right_img = np.frombuffer(nir_rg_image, dtype=np.uint8).reshape((480, 640))
        
        # horizontal stack
        #image=np.hstack((nir_lf_image, nir_rg_image))
        image = np.hstack((left_img, right_img))
        #cv2.namedWindow('NIR images (left, right)', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('stereo images', left_img)
        key = cv2.waitKey(1)
        # Press esc or 'q' to close the image window
        if key & 0xFF == ord('q') or key == 27:
            cv2.destroyAllWindows()
            break
finally:
    pipeline.stop()
