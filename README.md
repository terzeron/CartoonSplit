CartoonSplit
============

A utility set which splits the cartoon strip into multiple pieces.  
This utility is a python script made by using PIL (Python Image Library).  

Requirements
------------
PIL (Python Image Library)  
You can install this python module by
 > $ pip install PIL
 
or download from http://www.pythonware.com/products/pil.

Usage
-----
./split.py -n #unit [-b bandwidth] [-m margin] [-r] imagefile  
  	-n #unit: more than 2  
  	-b bandwidth: default 100  
  	-m margin: default 10  
  	-r: remove bouding box  

Tutorial
--------
 > $ split.py -n 5 -b 20 imagefile

There will be 5 sub images at maximum after splitting the original image file.  
The '-n' option specifies the maximum number of splitted sub images.  
The '-b' option specifies the width of split band.  
The '-m' option specifies the marginal size which can be ignored.  
The '-r' option is obsoleted for the PIL library functionality.  
  


