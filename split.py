#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import getopt
from PIL import Image
import operator
from math import pow
from typing import Tuple, List, Dict, Optional


default_bandwidth = 20 # 자르는 기준이 되는 띠의 두께
default_num_units = 1 # 1/n로 자를 때의 n의 갯수
default_margin = 0 # 이미지 가장자리 제외하는 여유공간의 크기
default_diff_threshold = 0.05 # 5%
default_size_threshold = 0 # 0 pixel
default_quality = 90


def sumup_pixels_in_box(im, sum_pixel, pixel_count, x1, y1, bandwidth) -> Tuple[List[int], int]:
    for i in range(x1, x1 + bandwidth):
        for j in range(y1, y1 + bandwidth):
            pixel = im.getpixel((i, j))
            sum_pixel[0] += pixel[0]
            sum_pixel[1] += pixel[1]
            sum_pixel[2] += pixel[2]
            pixel_count += 1
            return sum_pixel, pixel_count
        

def determine_bgcolor(im, bandwidth) -> Tuple[int, int, int]:
    (width, height) = im.size
    sum_pixel = [0, 0, 0]
    pixel_count = 0
    sum_pixel, pixel_count = sumup_pixels_in_box(im, sum_pixel, pixel_count, 0, 0, bandwidth)
    sum_pixel, pixel_count = sumup_pixels_in_box(im, sum_pixel, pixel_count, width - bandwidth, 0, bandwidth)
    sum_pixel, pixel_count = sumup_pixels_in_box(im, sum_pixel, pixel_count, 0, height - bandwidth, bandwidth)
    sum_pixel, pixel_count = sumup_pixels_in_box(im, sum_pixel, pixel_count, width - bandwidth, height - bandwidth, bandwidth)
    return int(sum_pixel[0] / pixel_count), int(sum_pixel[1] / pixel_count), int(sum_pixel[2] / pixel_count)


def determine_dominant_color(im) -> Tuple[int, int, int]:
    (width, height) = im.size
    color_counter: Dict[Tuple[int, int, int], int] = {}
    for i in range(0, width, max(int(width / 100), 1)):
        for j in range(0, height, max(int(height / 100), 1)):
            color = im.getpixel((i, j))
            if color in color_counter:
                color_counter[color] = color_counter[color] + 1
            else:
                color_counter[color] = 1
                sorted_counter = sorted(iter(color_counter.items()), key=operator.itemgetter(1))
    return sorted_counter[-1][0]


def get_euclidean_distance(a, b) -> float:
    return pow(a[0] - b[0], 2) + pow(a[1] - b[1], 2) + pow(a[2] - b[2], 2)


def get_color_distance(color_a, color_b, is_fuzzy) -> float:
    #print "get_color_distance, a=", color_a, ", b=", color_b
    color_white = (255, 255, 255)
    color_black = (0, 0, 0)
    if color_b == (-1, -1, -1):
        shade_of_color_a = (color_a[1] + color_a[1] + color_a[2]) / 3
        if shade_of_color_a < 128:
            color_b = color_black
        else:
            color_b = color_white
    distance = get_euclidean_distance(color_a, color_b)
    if is_fuzzy == True:
        distance_white = get_euclidean_distance(color_a, color_white)
        distance_black = get_euclidean_distance(color_a, color_black)
        distance = min(distance_white, distance_black, distance)
    return distance


def check_horizontal_band(im, x1, y1, bandwidth, bgcolor, margin, diff_threshold, is_fuzzy) -> Tuple[bool, int]:
    #print "check_horizontal_band(%d, %d)" % (x1, y1)
    (width, height) = im.size
    for j in range(y1, y1 + bandwidth):
        if j >= height:
            return (False, j - y1 + 1)
        diff_count = 0
        for i in range(x1 + margin, x1 + width - margin):
            pixel = im.getpixel((i, j))
            #print (i, j), pixel
            # 배경색과 불일치할 때 색상이 크게 차이나지 않으면 무시함
            if bgcolor == (-1, -1, -1):
                # blackorwhite
                if pixel == (0, 0, 0) or pixel == (255, 255, 255):
                    is_same = True
                else:
                    is_same = False
            else:
                # specific color
                if pixel == bgcolor:
                    is_same = True
                else:
                    is_same = False
            if not is_same:
                if get_color_distance(pixel, bgcolor, is_fuzzy) > 3.0:
                    diff_count += 1
                    #print "y1=%d, diff_count=%d, converted_threshold=%f" % (y1, diff_count, (width - 2 * margin) * diff_threshold)
                    # threshold 미만으로 불일치가 존재하면 false 반환
                    if diff_count > (width - 2 * margin) * diff_threshold:
                        return (False, j - y1 + 1)
    return (True, 0)


def check_vertical_band(im, x1, y1, bandwidth, bgcolor, margin, diff_threshold, is_fuzzy) -> Tuple[bool, int]:
    #print("check_vertical_band(%d, %d)" % (x1, y1))
    (width, height) = im.size
    for i in range(x1, x1 + bandwidth):
        if i >= width:
            return (False, i - x1 + 1)
        diff_count = 0
        for j in range(y1 + margin, y1 + height - margin):
            pixel = im.getpixel((i, j))
            #print (i, j), pixel
            # 배경색과 불일치할 때 색상이 크게 차이나지 않으면 무시함
            if bgcolor == (-1, -1, -1):
                # blackorwhite
                if pixel == (0, 0, 0) or pixel == (255, 255, 255):
                    is_same = True
                else:
                    is_same = False
            else:
                # specific color
                if pixel == bgcolor:
                    is_same = True
                else:
                    is_same = False
            if not is_same:
                distance = get_color_distance(pixel, bgcolor, is_fuzzy)
                if distance > 3.0:
                    diff_count += 1
                    #print("x1=%d, distance=%d, diff_count=%d, converted_threshold=%f" % (x1, distance, diff_count, (height - 2 * margin) * diff_threshold))
                    # threshold 미만으로 불일치가 존재하면 false 반환
                    if diff_count > (height - 2 * margin) * diff_threshold:
                        return (False, i - x1 + 1)
    return (True, 0)


def find_bgcolor_band(im, bgcolor, orientation, bandwidth, x1, y1, margin, diff_threshold, is_fuzzy) -> Tuple[int, int]:
    print("find_bgcolor_band(bgcolor=%s, orientation=%s, bandwidth=%d, x1=%d, y1=%d, diff_threshold=%f, is_fuzzy=%s)" % (bgcolor, orientation, bandwidth, x1, y1, diff_threshold, is_fuzzy))
    (width, height) = im.size
    if orientation == "vertical":
        # 세로 이미지인 경우
        i = 0
        while y1 + i < height:
            # 가로 띠가 배경색으로만 구성되었는지 확인
            (flag, offset) = check_horizontal_band(im, x1, y1 + i, bandwidth, bgcolor, margin, diff_threshold, is_fuzzy)
            if flag:
                return (x1, int(y1 + i + bandwidth / 2))
            i += offset
    elif orientation == "horizontal":
        # 가로 이미지인 경우
        i = 0
        while x1 + i < width:
            # 세로 띠가 배경색으로만 구성되었는지 확인
            (flag, offset) = check_vertical_band(im, x1 + i, y1, bandwidth, bgcolor, margin, diff_threshold, is_fuzzy)
            if flag:
                return (int(x1 + i + bandwidth / 2), y1)
            i += offset
    return (-1, -1)


def determine_color_option(a) -> Optional[Tuple[Optional[Tuple[int, int, int]], bool, bool]]:
    bgcolor: Optional[Tuple[int, int, int]] = None
    do_use_dominant_color = False
    is_fuzzy = False
    if a == "white":
        bgcolor = (255, 255, 255)
    elif a == "black":
        bgcolor = (0, 0, 0)
    elif a == "blackorwhite":
        bgcolor = (-1, -1, -1)
    elif a == "dominant":
        do_use_dominant_color = True
    elif a == "fuzzy":
        is_fuzzy = True
        do_use_dominant_color = True
    elif a[0] == "#":
        colorValue = int(a[1:], 16)
        bgcolor = (int(colorValue / 65536), int((colorValue % 65536) / 256), int(colorValue % 256))
    else:
        return None
    return (bgcolor, is_fuzzy, do_use_dominant_color)


def check_proportion(width, height, unit_width, orientation) -> bool:
    print("check_proportion(unit_width/2.0=%f, width=%f, height=%f, width/height=%f, height/width=%f)" % ((unit_width/2.0), width, height, (width/height) if height != 0 else 0, (height/width) if width != 0 else 0))
    if orientation == "horizontal":
        if width < float(unit_width / 2.0):
            return True
    else:
        if height < float(unit_width / 2.0):
            return True
    return False


def print_usage() -> None:
    print("_usage: %s -n #unit [-b <bandwidth>] [-m <margin>] [-c <bgcolor or method>] [-t <diff threshold>] [-v] <image file>" % (sys.argv[0]))
    print("\t-n <num units>: more than 2")
    print("\t-b <bandwidth>: (default %d)" % (default_bandwidth))
    print("\t-m <margin>: (default %d)" % (default_margin))
    print("\t-c <bgcolor or method>: 'white' or 'black', 'blackorwhite', 'dominant', 'fuzzy', '#135fd8', ...")
    print("\t\tblackorwhite: black or white")
    print("\t\tdominant: most dominant color (automatic)")
    print("\t\tfuzzy: either black, white or prevailing color (automatic)")
    print("\t-t <diff threshold>: diff threshold (default %f)" % (default_diff_threshold))
    print("\t-s <size threshold>: size threshold (default %d)" % (default_size_threshold))
    print("\t-v: split vertically")
    
            
def main() -> int:
    # 옵션 처리
    bandwidth = default_bandwidth
    num_units = default_num_units
    margin = default_margin
    diff_threshold = default_diff_threshold;
    size_threshold = default_size_threshold;
    bgcolor = None
    do_use_dominant_color = False
    is_fuzzy = False
    do_split_vertically = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hb:n:m:c:t:s:vi")
    except getopt.GetoptError:
        print_usage()
        sys.stderr.write("Error: invaild option definition\n")
        sys.exit(-1)
        
    for o, a in opts:
        if o == "-b":
            bandwidth = int(a)
        elif o == "-m":
            margin = int(a)
        elif o == "-n":
            num_units = int(a)
            if num_units < 2:
                print_usage()
                sys.stderr.write("Error: n must be more than 1\n")
                sys.exit(-1)
        elif o == "-c":
            color_option = determine_color_option(a)
            if not color_option:
                print_usage();
                sys.exit(-1)
            (bgcolor, is_fuzzy, do_use_dominant_color) = color_option
        elif o == "-t":
            diff_threshold = float(a)
        elif o == "-s":
            size_threshold = int(a)
        elif o == "-v":
            do_split_vertically = True
        else:
            print_usage()
            sys.exit(-1)
    if len(args) < 1:
        print_usage()
        sys.stderr.write("Error: The image file is not specified\n")
        sys.exit(-1)
    imageFile = args[0]
    (name_prefix, ext) = os.path.splitext(imageFile)
    print("bandwidth=", bandwidth)
    print("num_units=", num_units)
    print("margin=", margin)
    print("diff_threshold=", diff_threshold)
    #print("size_threshold=", size_threshold)
    print("arg=", args[0])

    im = Image.open(imageFile)
    format = im.format
    print("format=%s" % format)
    if im.mode != "RGB":
        im = im.convert("RGB")
    (width, height) = im.size
    print("width=%d, height=%d" % (width, height))
    if width > height or do_split_vertically:
        orientation = "horizontal"
    else:
        orientation = "vertical"
    print("orientation=", orientation)
    if orientation == "horizontal":
        unit_width = int((width - bandwidth * (num_units - 1)) / num_units)
    else:
        unit_width = int((height - bandwidth * (num_units - 1)) / num_units)
    print("unit_width=", unit_width)
    if do_use_dominant_color == True:
        bgcolor = determine_dominant_color(im)
    if bgcolor == None:
        bgcolor = determine_bgcolor(im, 10)
    print("bgcolor=", bgcolor)

    # size threshold check
    if orientation == "horizontal":
        if width <= size_threshold:
            return -1
    else:
        if height <= size_threshold:
            return -1
        
    (x0, y0) = (0, 0)
    (prev_x0, prev_y0) = (x0, y0)
    if num_units > 1:
        for i in range(0, num_units):
            print("\ni=%d, num_units=%d" % (i, num_units))
            if orientation == "horizontal":
                (x1, y1) = (int(max((unit_width + bandwidth) * (i + 1), x0 + unit_width)), y0)
            else:
                (x1, y1) = (x0, int(max((unit_width + bandwidth) * (i + 1), y0 + unit_width)))
            print("(x0, y0)=", (x0, y0))
            print("(x1, y1)=", (x1, y1))
            if x0 >= width - bandwidth or y0 >= height - bandwidth or x1 >= width - bandwidth or y1 >= height - bandwidth:
                break
            # 배경색으로만 구성된 띠를 찾아냄
            (x1, y1) = find_bgcolor_band(im, bgcolor, orientation, bandwidth, x1, y1, margin, diff_threshold, is_fuzzy)
            print("cutting point=", (x1, y1))
            if (x1, y1) == (-1, -1):
                print("Warning: no splitting")
                break

            sub_img_name = name_prefix + "." + str(i + 1) + ext
                    
            # 잘라서 저장
            if orientation == "horizontal":
                print("crop: x0=%d, y0=%d, x1=%d, height=%d" % (x0, y0, x1, height))
                subIm = im.crop((x0, y0, x1, height))
            else:
                print("crop: x0=%d, y0=%d, width=%d, y1=%d" % (x0, y0, width, y1))
                subIm = im.crop((x0, y0, width, y1))

            try:
                subIm.save(sub_img_name, quality=default_quality, format=format)
                last_saved_sub_img_name = sub_img_name
                print("save: " + sub_img_name)
            except SystemError:
                sys.stderr.write("Error: can't save the split image\n")
                return -1
            (prev_x0, prev_y0) = (x0, y0)
            (x0, y0) = (x1, y1)

        # 나머지 부분 저장
        print("last cutting point=", (width, height))
        if orientation == "horizontal":
            (x1, y1) = (width, 0)
        else:
            (x1, y1) = (0, height)

        sub_img_name = name_prefix + "." + str(i + 1) + ext

        # 마지막 남은 조각의 경우, 너무 얇다면 이전 조각에 붙여서 다시 저장
        is_too_thin = check_proportion(x1 - x0, y1 - y0, unit_width, orientation)
        if is_too_thin:
            print("too thin slice - merge with previous")
            sub_img_name = last_saved_sub_img_name
            (x0, y0) = (prev_x0, prev_y0)

        print("crop: x0=%d, y0=%d, width=%d, height=%d" % (x0, y0, width, height))
        subIm = im.crop((x0, y0, width, height))
        try:
            subIm.save(sub_img_name, quality=default_quality, format=format)
            print("save: " + sub_img_name)
        except SystemError:
            sys.stderr.write("Error: can't save the split image\n")
            return -1
        
    return 0

        
if __name__ == "__main__":
    sys.exit(main())
