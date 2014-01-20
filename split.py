#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import getopt
import Image
from math import pow


default_band_width = 100 # 자르는 기준이 되는 띠의 두께
default_num_units = 1 # 1/n로 자를 때의 n의 갯수
default_margin = 0 # 이미지 가장자리 제외하는 여유공간의 크기
diff_threshold = 0.005 # 0.5%


def sumup_pixels_in_box(im, sum_pixel, pixel_count, x1, y1, band_width):
	for i in range(x1, x1 + band_width):
		for j in range(y1, y1 + band_width):
			pixel = im.getpixel((i, j))
			sum_pixel[0] += pixel[0]
			sum_pixel[1] += pixel[1]
			sum_pixel[2] += pixel[2]
			pixel_count += 1
			return (sum_pixel, pixel_count)
		

def determine_bgcolor(im, band_width):
	(width, height) = im.size
	sum_pixel = [0, 0, 0]
	pixel_count = 0
	(sum_pixel, pixel_count) = sumup_pixels_in_box(im, sum_pixel, pixel_count, 0, 0, band_width)
	(sum_pixel, pixel_count) = sumup_pixels_in_box(im, sum_pixel, pixel_count, width - band_width, 0, band_width)
	(sum_pixel, pixel_count) = sumup_pixels_in_box(im, sum_pixel, pixel_count, 0, height - band_width, band_width)
	(sum_pixel, pixel_count) = sumup_pixels_in_box(im, sum_pixel, pixel_count, width - band_width, height - band_width, band_width)
	return (sum_pixel[0] / pixel_count, sum_pixel[1] / pixel_count, sum_pixel[2] / pixel_count)


def get_color_distance(color_a, color_b):
	return pow(color_a[0] - color_b[0], 2) + pow(color_a[1] - color_b[1], 2) + pow(color_a[2] - color_b[2], 2)


def check_horizontal_band(im, x1, y1, band_width, bgcolor, margin):
	#print "check_horizontal_band(%d, %d)" % (x1, y1)
	(width, height) = im.size
	for j in range(y1, y1 + band_width):
		if j >= height:
			return (False, j - y1 + 1)
		diff_count = 0
		for i in range(x1 + margin, x1 + width - margin):
			pixel = im.getpixel((i, j))
			#print (i, j), pixel
			# 배경색과 불일치할 때 색상이 크게 차이나지 않으면 무시함
			if pixel != bgcolor:
				if get_color_distance(pixel, bgcolor) > 9.0:
					diff_count += 1
					#print y1, diff_count
					# threshold 미만으로 불일치가 존재하면 false 반환
					if diff_count > (width - 2 * margin) * diff_threshold:
						return (False, j - y1 + 1)
	return (True, 0)


def check_vertical_band(im, x1, y1, band_width, bgcolor, margin):
	#print "check_vertical_band(%d, %d)" % (x1, y1)
	(width, height) = im.size
	for i in range(x1, x1 + band_width):
		if i >= width:
			return (False, i - x1 + 1)
		diff_count = 0
		for j in range(y1 + margin, y1 + height - margin):
			pixel = im.getpixel((i, j))
			#print (i, j), pixel
			# 배경색과 불일치할 때 색상이 크게 차이나지 않으면 무시함
			if pixel != bgcolor:
				if get_color_distance(pixel, bgcolor) > 9.0:
					diff_count += 1
					#print x1, diff_count
					# threshold 미만으로 불일치가 존재하면 false 반환
					if diff_count > (height - 2 * margin) * diff_threshold:
						return (False, i - x1 + 1)
	return (True, 0)

                
def find_bgcolor_band(im, bgcolor, orientation, band_width, x1, y1, margin):
	(width, height) = im.size
	if orientation == "vertical":
		# 세로 이미지인 경우
		i = 0
		while y1 + i < height:
			# 가로 띠가 배경색으로만 구성되었는지 확인
			(flag, offset) = check_horizontal_band(im, x1, y1 + i, band_width, bgcolor, margin)
			if flag:
				return (x1, y1 + i + band_width / 2)
			i += offset
	elif orientation == "horizontal":
		# 가로 이미지인 경우
		i = 0
		while x1 + i < width:
			# 세로 띠가 배경색으로만 구성되었는지 확인
			(flag, offset) = check_vertical_band(im, x1 + i, y1, band_width, bgcolor, margin)
			if flag:
				return (x1 + i + band_width / 2, y1)
			i += offset
	return (-1, -1)


def print_usage():
	print "Usage: %s -n #unit [-b bandwidth] [-m margin] [-c bgcolor] [-r] imagefile" % (sys.argv[0])
	print "\t-n #unit: more than 2"
	print "\t-b bandwidth: default 100"
	print "\t-m margin: default 10"
	print "\t-c bgcolor: white or black"
	print "\t-r: remove bouding box"
	
			
def main():
	# 옵션 처리
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hb:n:m:c:r")
	except getopt.GetoptError as err:
		print_usage()
		print "Invaild option definition"
		sys.exit(-1)
	band_width = default_band_width
	num_units = default_num_units
	margin = default_margin
	bgcolor = None
	do_remove_bounding_box = False
	for o, a in opts:
		if o == "-b":
			band_width = int(a)
		elif o == "-m":
			margin = int(a)
		elif o == "-n":
			num_units = int(a)
			if num_units < 2:
				print_usage()
				print "n must be more than 1"
				sys.exit(-1)
		elif o == "-r":
			do_remove_bounding_box = True
		elif o == "-c":
			if a == "white":
				bgcolor = (255, 255, 255)
			elif a == "black":
				bgcolor = (0, 0, 0)
		else:
			print_usage()
			print "Unknown option"
			sys.exit(-1)
	if len(args) < 1:
		print_usage()
		print "The image file is not specified"
		sys.exit(-1)
	image_file = args[0]
	(name_prefix, ext) = os.path.splitext(image_file)
	print "band_width=", band_width
	print "num_units=", num_units
	print "margin=", margin
	print "arg=", args[0]
            
	# 이미지를 열고
	im = Image.open(image_file)
	(width, height) = im.size
	print "width=%d, height=%d" % (width, height)
	# 배경색을 결정함
	if bgcolor == None:
		bgcolor = determine_bgcolor(im, 10)
	print "bgcolor=", bgcolor
		
	(x0, y0) = (0, 0)
	if width > height:
		orientation = "horizontal"
	else:
		orientation = "vertical"
	print "orientation=", orientation
	if num_units > 1:
		for i in range(0, num_units):
			if orientation == "horizontal":
				(x1, y1) = (((i + 1) * width - band_width * num_units) / num_units, y0)
			else:
				(x1, y1) = (x0, ((i + 1) * height - band_width * num_units)/ num_units)
			print "(x0, y0)=", (x0, y0)
			print "(x1, y1)=", (x1, y1)
			if x0 >= width - band_width or y0 >= height - band_width or x1 >= width - band_width or y1 >= height - band_width:
				break
			# 배경색으로만 구성된 띠를 찾아냄
			(x1, y1) = find_bgcolor_band(im, bgcolor, orientation, band_width, x1, y1, margin)
			print "cutting point=", (x1, y1)
			if (x1, y1) == (-1, -1):
				print "Error: no splitting"
				break
			# 잘라서 저장
			if orientation == "horizontal":
				sub_im = im.crop((x0, y0, x1, height))
			else:
				sub_im = im.crop((x0, y0, width, y1))
			if do_remove_bounding_box:
				quadruple = sub_im.getbbox()
				if quadruple:
					sub_im = sub_im.crop(quadruple)
			try:
				sub_im.save(name_prefix + "." + str(i + 1) + ext, quality=95)
			except SystemError:
				break
			(x0, y0) = (x1, y1)
			print
		# 나머지 부분 저장
		print "last cutting point=", (width, height)
		sub_im = im.crop((x0, y0, width, height))
		if do_remove_bounding_box:
			quadruple = sub_im.getbbox()
			if quadruple:
				sub_im = sub_im.crop(quadruple)
		sub_im.save(name_prefix + "." + str(i + 1) + ext, quality=95)

        
if __name__ == "__main__":
	main()
