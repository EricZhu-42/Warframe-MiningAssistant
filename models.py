import cv2 as cv
import imutils
import numpy as np
from matplotlib import pyplot as plt

from utils import cumulative_diff, moving_average


class ImageTransformer(object):
    def __init__(self, width=2560, height=1440):
        self.width = width
        self.height = height
        self.radius = int(width * 0.097)

        self.focus_shape = (self.radius * 2, self.radius * 2)
        self.focus_center = (self.radius, self.radius)

        self.monitor = {
            "top": int(self.height / 2 - self.radius),
            "left": int(self.width / 2 - self.radius),
            "width": self.radius * 2,
            "height": self.radius * 2,
        }

    def extract_focus(self, img):
        width_center = int(self.width / 2)
        height_center = int(self.height / 2)

        x_start = width_center - self.radius
        x_end = width_center + self.radius
        y_start = height_center - self.radius
        y_end = height_center + self.radius

        img = img[y_start:y_end, x_start:x_end]
        return img

    def polar_transform(self, img):
        assert img.shape[0] == img.shape[1]
        img = imutils.rotate(img, 90)
        img = cv.warpPolar(
            img, self.focus_shape, self.focus_center, self.radius, cv.WARP_POLAR_LINEAR
        )
        img = imutils.rotate(img, 90)
        img = img[
            : int(self.radius * 0.77),
            int(self.radius * 0.04) : -int(self.radius * 0.04),
        ]
        return img


class ImageEvaluator(object):
    def __init__(self, draw=False):
        self.progress = 0
        self.drawed_img = None
        self.draw = draw

    def __draw_line(self, x, r=0, g=0, b=0):
        return cv.line(
            self.drawed_img,
            (x, 0),
            (x, self.drawed_img.shape[0]),
            (255 * b, 255 * g, 255 * r),
            3,
        )

    def compute_difference(self, img):
        if self.draw:
            self.drawed_img = img.copy()

        x_progress = self.find_progress(img)
        max_progress = img.shape[1]

        is_non_crit, x_target = self.find_noncrit(img)
        is_crit, x_target = self.find_crit(img)
        if not is_crit:
            is_non_crit, x_target = self.find_noncrit(img)
            if not is_non_crit:
                return max_progress

        return x_target - x_progress

    def find_progress(self, img):
        height, width = img.shape[:2]
        img = img[int(0.35 * height) : int(0.65 * height), :]

        img = cv.cvtColor(img, cv.COLOR_BGR2HSV)
        img = img[:, :, 2]
        cv.imwrite("progress.png", img)

        data = np.average(img, axis=0)
        data = moving_average(data, n=19)
        data = cumulative_diff(data, n=11)

        candidates = np.where(data < -30)[0]
        if len(candidates):
            self.progress = candidates[0] + int(width * 0.044)
            if self.draw:
                self.__draw_line(self.progress, b=1)
        else:
            self.progress = 0

        return self.progress

    def find_crit(self, img):
        height = img.shape[0]
        img = img[int(0.45 * height) : int(0.55 * height), self.progress + 1 :]

        img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        _, img = cv.threshold(img, 210, 255, cv.THRESH_BINARY)

        avg_value = np.average(img, axis=0)
        maximum_x_index = np.argmax(avg_value)
        maximum_x_value = avg_value[maximum_x_index]
        maximum_x_index += self.progress + 1

        if maximum_x_value > 120:
            if self.draw:
                self.__draw_line(maximum_x_index, r=1)
            return (True, maximum_x_index)
        else:
            return (False, 0)

    def find_noncrit(self, img):
        height, width = img.shape[:2]
        img = img[int(0.10 * height) : int(0.3 * height), :]

        img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        _, img = cv.threshold(img, 210, 255, cv.THRESH_BINARY)

        avg_value = np.average(img, axis=0)
        left, right = np.argsort(avg_value)[-2:]

        if min(avg_value[left], avg_value[right]) > 180:
            target_x = int((left + right) / 2)
            if self.draw:
                self.__draw_line(target_x, g=1)
            return (True, target_x)
        else:
            return (False, 0)
