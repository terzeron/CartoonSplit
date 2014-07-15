#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PIL import Image


def print_usage():
	print "Usage: %s imagefile" % (sys.argv[0])
	
			
def main():
	im = Image.open(sys.argv[1])
	print im.size[0], im.size[1]

        
if __name__ == "__main__":
	main()
