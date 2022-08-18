import argparse
import time

import cv2 as cv
import mss
import numpy as np
from pynput.mouse import Button, Controller

from models import ImageEvaluator, ImageTransformer

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--show", action="store_true", help="show real-time images")
args = parser.parse_args()
show = args.show

transformer = ImageTransformer(width=2560, height=1440)
evaluator = ImageEvaluator(show=show)
monitor = transformer.monitor
controller = Controller()

with mss.mss() as sct:

    while "Screen capturing":

        target_area = np.array(sct.grab(monitor))
        transformed = transformer.polar_transform(target_area)
        diff = evaluator.compute_difference(transformed)

        if show:
            cv.imshow("Target Area", target_area)
            cv.imshow("Transformed", transformed)
            cv.imshow("Detected", evaluator.drawed_img)

        if diff <= 10:
            time.sleep(0.03)
            controller.release(Button.left)

        if cv.waitKey(25) & 0xFF == ord("q"):
            cv.destroyAllWindows()
            break
