import pyrealsense2 as rs
import numpy as np
import cv2

# Configure and start the pipeline
pipeline = rs.pipeline()
config = rs.config()

# Enable the color stream 
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

pipeline.start(config)

try:
    while True:
        # Get frameset from the pipeline
        frames = pipeline.wait_for_frames()

        # Get the color frame
        color_frame = frames.get_color_frame()

        # Convert the frame to a numpy array
        color_image = np.asanyarray(color_frame.get_data())

        # Display the color frame
        cv2.imshow('Color Frame', color_image)

        # Exit on 'q' key press
        if cv2.waitKey(1) == ord('q'):
            break

finally:
    # Stop the pipeline and close the window
    pipeline.stop()
    cv2.destroyAllWindows()
