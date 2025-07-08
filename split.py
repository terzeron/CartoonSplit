#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import getopt
from PIL import Image
import operator
from math import pow
from typing import Tuple, List, Dict, Optional


Image.MAX_IMAGE_PIXELS = None
default_bandwidth = 20 # 자르는 기준이 되는 띠의 두께
default_num_units = 1 # 1/n로 자를 때의 n의 갯수
default_margin = 0 # 이미지 가장자리 제외하는 여유공간의 크기
default_diff_threshold = 0.05 # 5%, 띠를 구성하는 픽셀들의 불일치 허용율
default_size_threshold = 0 # 0 pixel, 분할 대상으로 간주할 최소한의 크기
default_acceptable_diff_of_color_value = 1
default_quality = 90

# WebP 최적화 상수
WEBP_MAX_DIMENSION = 8000  # WebP 권장 최대 크기
WEBP_MAX_PIXELS = 32000000  # 32MP (약 8000x4000)
WEBP_MEMORY_MULTIPLIER = 8  # WebP 인코딩에 필요한 메모리 배수


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


def check_horizontal_band(im, x1, y1, bandwidth, bgcolor, margin, diff_threshold, acceptable_diff_of_color_value, is_fuzzy) -> Tuple[bool, int]:
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
                distance = get_color_distance(pixel, bgcolor, is_fuzzy)
                if distance > 3 * pow(acceptable_diff_of_color_value, 2):
                    diff_count += 1
                    #print "y1=%d, diff_count=%d, converted_threshold=%f" % (y1, diff_count, (width - 2 * margin) * diff_threshold)
                    # threshold 미만으로 불일치가 존재하면 false 반환
                    if diff_count > (width - 2 * margin) * diff_threshold:
                        return (False, j - y1 + 1)
    return (True, 0)


def check_vertical_band(im, x1, y1, bandwidth, bgcolor, margin, diff_threshold, acceptable_diff_of_color_value, is_fuzzy) -> Tuple[bool, int]:
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
                if distance > 3 * pow(acceptable_diff_of_color_value, 2):
                    diff_count += 1
                    #print("x1=%d, distance=%d, diff_count=%d, converted_threshold=%f" % (x1, distance, diff_count, (height - 2 * margin) * diff_threshold))
                    # threshold 미만으로 불일치가 존재하면 false 반환
                    if diff_count > (height - 2 * margin) * diff_threshold:
                        return (False, i - x1 + 1)
    return (True, 0)


def find_bgcolor_band(im, bgcolor, orientation, bandwidth, x1, y1, margin, diff_threshold, acceptable_diff_of_color_value, is_fuzzy) -> Tuple[int, int]:
    print("find_bgcolor_band(bgcolor=%s, orientation=%s, bandwidth=%d, x1=%d, y1=%d, diff_threshold=%f, is_fuzzy=%s)" % (bgcolor, orientation, bandwidth, x1, y1, diff_threshold, is_fuzzy))
    (width, height) = im.size
    if orientation == "vertical":
        # 세로 이미지인 경우
        i = 0
        while y1 + i < height:
            # 가로 띠가 배경색으로만 구성되었는지 확인
            (flag, offset) = check_horizontal_band(im, x1, y1 + i, bandwidth, bgcolor, margin, diff_threshold, acceptable_diff_of_color_value, is_fuzzy)
            if flag:
                return (x1, int(y1 + i + bandwidth / 2))
            i += offset
    elif orientation == "horizontal":
        # 가로 이미지인 경우
        i = 0
        while x1 + i < width:
            # 세로 띠가 배경색으로만 구성되었는지 확인
            (flag, offset) = check_vertical_band(im, x1 + i, y1, bandwidth, bgcolor, margin, diff_threshold, acceptable_diff_of_color_value, is_fuzzy)
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


def optimize_image_for_webp(subIm):
    """Optimize image to ensure WebP compatibility"""
    try:
        # Ensure image is in RGB mode
        if subIm.mode != 'RGB':
            subIm = subIm.convert('RGB')
        
        width, height = subIm.size
        total_pixels = width * height
        
        # Check if image needs optimization
        needs_resize = False
        new_width, new_height = width, height
        
        # Check dimension limits
        if width > WEBP_MAX_DIMENSION or height > WEBP_MAX_DIMENSION:
            needs_resize = True
            if width > height:
                new_width = WEBP_MAX_DIMENSION
                new_height = int(height * WEBP_MAX_DIMENSION / width)
            else:
                new_height = WEBP_MAX_DIMENSION
                new_width = int(width * WEBP_MAX_DIMENSION / height)
        
        # Check pixel count limits
        elif total_pixels > WEBP_MAX_PIXELS:
            needs_resize = True
            scale_factor = (WEBP_MAX_PIXELS / total_pixels) ** 0.5
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
        
        # Apply resize if needed
        if needs_resize:
            print(f"Optimizing image from {width}x{height} to {new_width}x{new_height} for WebP compatibility")
            subIm = subIm.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return subIm
        
    except Exception as e:
        print(f"Error optimizing image: {e}")
        return subIm


def save_webp_guaranteed(subIm, sub_img_name):
    """Save image as WebP with guaranteed success using multiple fallback strategies"""
    try:
        # Strategy 1: Try with optimized image and conservative settings
        optimized_im = optimize_image_for_webp(subIm)
        final_width, final_height = optimized_im.size
        print(f"Attempting WebP save: {sub_img_name} ({final_width}x{final_height})")
        
        try:
            optimized_im.save(
                sub_img_name, 
                format='WEBP', 
                quality=80,      # Lower quality for better compatibility
                method=0,        # Most reliable method
                lossless=False,
                exact=False
            )
            print(f"Successfully saved WebP: {sub_img_name}")
            return True
        except Exception as e1:
            print(f"WebP method=0 failed: {e1}")
            
        # Strategy 2: Try with even lower quality
        try:
            optimized_im.save(
                sub_img_name, 
                format='WEBP', 
                quality=70,
                method=1,
                lossless=False,
                exact=False
            )
            print(f"Successfully saved WebP (method=1): {sub_img_name}")
            return True
        except Exception as e2:
            print(f"WebP method=1 failed: {e2}")
            
        # Strategy 3: Try with lossless compression
        try:
            optimized_im.save(
                sub_img_name, 
                format='WEBP', 
                lossless=True,
                method=0
            )
            print(f"Successfully saved lossless WebP: {sub_img_name}")
            return True
        except Exception as e3:
            print(f"Lossless WebP failed: {e3}")
            
        # Strategy 4: Try with original image (no optimization)
        try:
            if subIm.mode != 'RGB':
                subIm = subIm.convert('RGB')
            subIm.save(
                sub_img_name, 
                format='WEBP', 
                quality=60,
                method=0
            )
            print(f"Successfully saved WebP (original): {sub_img_name}")
            return True
        except Exception as e4:
            print(f"Original image WebP failed: {e4}")
            
        # Strategy 5: Try with PNG as fallback (WebP-like compression)
        try:
            png_name = sub_img_name.replace('.webp', '.png')
            optimized_im.save(png_name, format='PNG', optimize=True)
            print(f"Saved as PNG fallback: {png_name}")
            return True
        except Exception as e5:
            print(f"PNG fallback failed: {e5}")
            
        return False
        
    except Exception as e:
        print(f"WebP save completely failed for {sub_img_name}: {e}")
        return False


def save_image_safely(subIm, sub_img_name, original_format):
    """Save image with guaranteed success using multiple formats"""
    try:
        # Try WebP first with multiple fallback strategies
        if save_webp_guaranteed(subIm, sub_img_name):
            return True
        
        # If WebP completely fails, use original format
        print(f"WebP failed, using original format {original_format} for {sub_img_name}")
        
        # Ensure image is in correct mode
        if subIm.mode != 'RGB':
            subIm = subIm.convert('RGB')
        
        if original_format and original_format.upper() in ['JPEG', 'JPG']:
            subIm.save(sub_img_name, quality=85, format='JPEG', optimize=True)
        elif original_format and original_format.upper() == 'PNG':
            subIm.save(sub_img_name, format='PNG', optimize=True)
        else:
            # Default to JPEG if original format is not supported
            subIm.save(sub_img_name, quality=85, format='JPEG', optimize=True)
        
        print(f"Successfully saved as {original_format or 'JPEG'}: {sub_img_name}")
        return True
        
    except Exception as e:
        print(f"All save methods failed for {sub_img_name}: {e}")
        return False


def print_usage(program_name: str) -> None:
    print("usage: %s -n #unit" % program_name)
    print("          [-b <bandwidth>] [-m <margin>]")
    print("          [-c <bgcolor or method>] [-t <diff threshold>]")
    print("          [-s <size_threshold] [-a <acceptable diff of color value>]")
    print("          [-v] [-w] <image file>")
    print("\t-n <num units>: more than 2")
    print("\t-b <bandwidth>: (default %d)" % (default_bandwidth))
    print("\t-m <margin>: (default %d)" % (default_margin))
    print("\t-c <bgcolor or method>: 'white' or 'black', 'blackorwhite', 'dominant', 'fuzzy', '#135fd8', ...")
    print("\t\tblackorwhite: black or white")
    print("\t\tdominant: most dominant color (automatic)")
    print("\t\tfuzzy: either black, white or prevailing color (automatic)")
    print("\t-t <diff threshold>: diff threshold (default %f)" % (default_diff_threshold))
    print("\t-s <size threshold>: size threshold (default %d)" % (default_size_threshold))
    print("\t-a <diff of color value>: acceptable diff of color value (default %d)" % (default_acceptable_diff_of_color_value))
    print("\t-v: split vertically")
    print("\t-w: scan range wider than fixed unit edge")
    
            
def main() -> int:
    # 옵션 처리
    bandwidth: int = default_bandwidth
    num_units: int = default_num_units
    margin: int = default_margin
    diff_threshold: float = default_diff_threshold;
    size_threshold: float = default_size_threshold;
    acceptable_diff_of_color_value: int = default_acceptable_diff_of_color_value
    bgcolor: Optional[Tuple[int, int, int]] = None
    do_use_dominant_color: bool = False
    is_fuzzy: bool = False
    do_split_vertically: bool = False
    do_scan_wider:bool = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hb:n:m:c:t:s:a:vwi")
    except getopt.GetoptError:
        print_usage(sys.argv[0])
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
        elif o == "-a":
            acceptable_diff_of_color_value = int(a)
        elif o == "-v":
            do_split_vertically = True
        elif o == "-w":
            do_scan_wider = True
        else:
            print_usage(sys.argv[0])
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
    print("size_threshold=", size_threshold)
    print("acceptable_diff_of_color_value=", acceptable_diff_of_color_value)
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
    cutting_points = []  # Store all cutting points
    actual_units_created = 0  # Track actual number of units created
    
    if num_units > 1:
        for i in range(0, num_units - 1):  # Changed: only go up to num_units - 1
            print("\ni=%d, num_units=%d" % (i, num_units))
            if orientation == "horizontal":
                (x1, y1) = (int(max((unit_width + bandwidth) * (i + 1), x0 + unit_width)), y0)
                if do_scan_wider:
                    (x1, y1) = (int(x1 * 0.9), y1)
            else:
                (x1, y1) = (x0, int(max((unit_width + bandwidth) * (i + 1), y0 + unit_width)))
                if do_scan_wider:
                    (x1, y1) = (x1, int(y1 * 0.9))
            print("(x0, y0)=", (x0, y0))
            print("(x1, y1)=", (x1, y1))
            
            # Ensure we don't exceed image boundaries
            if orientation == "horizontal":
                if x1 >= width - bandwidth:
                    x1 = width
                if x0 >= width - bandwidth:
                    print(f"Reached end of image at x0={x0}, width={width}")
                    break
            else:
                if y1 >= height - bandwidth:
                    y1 = height
                if y0 >= height - bandwidth:
                    print(f"Reached end of image at y0={y0}, height={height}")
                    break
                    
            # 배경색으로만 구성된 띠를 찾아냄
            (x1, y1) = find_bgcolor_band(im, bgcolor, orientation, bandwidth, x1, y1, margin, diff_threshold, acceptable_diff_of_color_value, is_fuzzy)
            print("cutting point=", (x1, y1))
            
            # If no suitable cutting point found, use calculated position
            if (x1, y1) == (-1, -1):
                if orientation == "horizontal":
                    x1 = min(width, int((width * (i + 1)) / num_units))
                else:
                    y1 = min(height, int((height * (i + 1)) / num_units))
                print("Using fallback cutting point=", (x1, y1))

            # Ensure coordinates are valid and within image bounds
            if orientation == "horizontal":
                if x1 <= x0:
                    x1 = width
                if x0 < 0:
                    x0 = 0
                if x1 > width:
                    x1 = width
            else:
                if y1 <= y0:
                    y1 = height
                if y0 < 0:
                    y0 = 0
                if y1 > height:
                    y1 = height

            # Additional safety check: if we're at the end of the image, break
            if orientation == "horizontal":
                if x0 >= width:
                    print(f"Reached end of image at x0={x0}, width={width}")
                    break
            else:
                if y0 >= height:
                    print(f"Reached end of image at y0={y0}, height={height}")
                    break

            cutting_points.append((x0, y0, x1, y1))
            sub_img_name = name_prefix + "." + str(i + 1) + ext
                    
            # 잘라서 저장
            if orientation == "horizontal":
                print("crop: x0=%d, y0=%d, x1=%d, height=%d" % (x0, y0, x1, height))
                # Ensure valid crop coordinates
                if x1 > x0 and x0 >= 0 and x1 <= width:
                    subIm = im.crop((x0, y0, x1, height))
                else:
                    print(f"Invalid crop coordinates: x0={x0}, x1={x1}, width={width}")
                    sys.stderr.write("Error: invalid crop coordinates\n")
                    return -1
            else:
                print("crop: x0=%d, y0=%d, width=%d, y1=%d" % (x0, y0, width, y1))
                # Ensure valid crop coordinates
                if y1 > y0 and y0 >= 0 and y1 <= height:
                    subIm = im.crop((x0, y0, width, y1))
                else:
                    print(f"Invalid crop coordinates: y0={y0}, y1={y1}, height={height}")
                    sys.stderr.write("Error: invalid crop coordinates\n")
                    return -1

            # Check if cropped image is valid
            if subIm.size[0] <= 0 or subIm.size[1] <= 0:
                print(f"Invalid cropped image size: {subIm.size}")
                sys.stderr.write("Error: cropped image has zero size\n")
                return -1

            # Save with WebP fallback
            try:
                subIm.save(sub_img_name, quality=default_quality, format=format)
            except Exception as e:
                print(f"Failed to save as {format}: {e}")
                # Try WebP with lower quality
                try:
                    subIm.save(sub_img_name, quality=80, format='WEBP')
                except Exception as e2:
                    print(f"Failed to save as WebP: {e2}")
                    # Final fallback to JPEG
                    try:
                        subIm.save(sub_img_name, quality=85, format='JPEG')
                    except Exception as e3:
                        print(f"All save methods failed: {e3}")
                        sys.stderr.write("Error: can't save the split image\n")
                        return -1
            
            print("save: " + sub_img_name)
            actual_units_created += 1
            (x0, y0) = (x1, y1)

        # 마지막 조각 저장 (필요한 경우에만)
        print("Checking if final piece is needed...")
        
        # Check if we need a final piece
        needs_final_piece = False
        if orientation == "horizontal":
            if x0 < width:
                needs_final_piece = True
        else:
            if y0 < height:
                needs_final_piece = True
        
        if needs_final_piece:
            print("Creating final piece...")
            sub_img_name = name_prefix + "." + str(actual_units_created + 1) + ext

            # 마지막 조각 저장
            if orientation == "horizontal":
                print("crop: x0=%d, y0=%d, width=%d, height=%d" % (x0, y0, width, height))
                if x0 < width:
                    subIm = im.crop((x0, y0, width, height))
                else:
                    print("Final crop would result in empty image")
                    sys.stderr.write("Error: final crop would be empty\n")
                    return -1
            else:
                print("crop: x0=%d, y0=%d, width=%d, height=%d" % (x0, y0, width, height))
                if y0 < height:
                    subIm = im.crop((x0, y0, width, height))
                else:
                    print("Final crop would result in empty image")
                    sys.stderr.write("Error: final crop would be empty\n")
                    return -1
                
            # Check if final cropped image is valid
            if subIm.size[0] <= 0 or subIm.size[1] <= 0:
                print(f"Invalid final cropped image size: {subIm.size}")
                sys.stderr.write("Error: final cropped image has zero size\n")
                return -1
                
            # Save with WebP fallback
            try:
                subIm.save(sub_img_name, quality=default_quality, format=format)
            except Exception as e:
                print(f"Failed to save as {format}: {e}")
                # Try WebP with lower quality
                try:
                    subIm.save(sub_img_name, quality=80, format='WEBP')
                except Exception as e2:
                    print(f"Failed to save as WebP: {e2}")
                    # Final fallback to JPEG
                    try:
                        subIm.save(sub_img_name, quality=85, format='JPEG')
                    except Exception as e3:
                        print(f"All save methods failed: {e3}")
                        sys.stderr.write("Error: can't save the split image\n")
                        return -1
            
            print("save: " + sub_img_name)
            actual_units_created += 1
        else:
            print("No final piece needed - image already fully processed")
        
    print(f"Total units created: {actual_units_created}")
    return 0

        
if __name__ == "__main__":
    sys.exit(main())
