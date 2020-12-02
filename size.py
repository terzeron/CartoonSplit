#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PIL import Image


def print_usage():
	print("Usage: %s imagefile" % (sys.argv[0]))
	
			
def main():
	im = Image.open(sys.argv[1])
	print("%d %d %s" % (im.size[0], im.size[1], im.format))

        
if __name__ == "__main__":
	main()
