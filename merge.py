#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PIL import Image


def print_usage():
	print "Usage: %s new old..." % (sys.argv[0])
	
			
def main():
	count = len(sys.argv[2:])
	im = []
	total_width = 0
	total_height = 0
	for i in range(count):
		print sys.argv[i + 2]
		im.append(Image.open(sys.argv[i + 2]))
		(width, height) = im[i].size
		print width, height
		if total_width < width:
			total_width = width
		total_height += height

	print total_width, total_height
	new_im = Image.new("RGB", (total_width, total_height), "white");
	box = (0, 0)
	total_height = 0
	for a_im in im:
		new_im.paste(a_im, box)
		(width, height) = a_im.size
		total_height += height
		box = (0, total_height)
		print "box=", box
	new_im.save(sys.argv[1], quality=95)

        
if __name__ == "__main__":
	main()
