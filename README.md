CartoonSplit
============

A utility set which splits the cartoon strip into multiple pieces.  
This utility is a python script made by using PIL (Python Image Library).  

Requirements
------------
Pillow: PIL (Python Image Library) fork
You can install this python module by
 > $ pip install pillow
 
or download from https://pillow.readthedocs.org/en/latest

Usage
-----
./split.py -n #unit [-b bandwidth] [-m margin] [-t threshold] imagefile  
  	-n #unit: more than 2  
  	-b bandwidth: default 100  
  	-m margin: default 10  
	-c color: background color
		You may use some pre-defined value 'blackorwhite', 'dominant', or 'fuzzy'.
	-t threshold: diff threshold (default 0.05; 5%)

Tutorial
--------
 > $ split.py -n 5 -b 20 imagefile

There will be 5 sub images at maximum after splitting the original image file.  
The '-n' option specifies the maximum number of splitted sub images.  
The '-b' option specifies the width of split band.  
The '-m' option specifies the marginal size which can be ignored.  
The '-c' option specifies the background color.
The '-t' option specifies the differential threshold.
  
 > $ merge.py newimagefile subimagefile1 subimagefile2 ...

You can merge some image files to a new big file.


