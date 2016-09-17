#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import getopt
from PIL import Image, ImageStat
import operator
from math import pow, sqrt


defaultBandWith = 20 # 자르는 기준이 되는 띠의 두께
defaultNumUnits = 1 # 1/n로 자를 때의 n의 갯수
defaultMargin = 0 # 이미지 가장자리 제외하는 여유공간의 크기
defaultDiffThreshold = 0.05 # 5%
defaultQuality = 90


def sumupPixelsInBox(im, sumPixel, pixelCount, x1, y1, bandWidth):
    for i in range(x1, x1 + bandWidth):
        for j in range(y1, y1 + bandWidth):
            pixel = im.getpixel((i, j))
            sumPixel[0] += pixel[0]
            sumPixel[1] += pixel[1]
            sumPixel[2] += pixel[2]
            pixelCount += 1
            return (sumPixel, pixelCount)
        

def determineBgcolor(im, bandWidth):
    (width, height) = im.size
    sumPixel = [0, 0, 0]
    pixelCount = 0
    (sumPixel, pixelCount) = sumupPixelsInBox(im, sumPixel, pixelCount, 0, 0, bandWidth)
    (sumPixel, pixelCount) = sumupPixelsInBox(im, sumPixel, pixelCount, width - bandWidth, 0, bandWidth)
    (sumPixel, pixelCount) = sumupPixelsInBox(im, sumPixel, pixelCount, 0, height - bandWidth, bandWidth)
    (sumPixel, pixelCount) = sumupPixelsInBox(im, sumPixel, pixelCount, width - bandWidth, height - bandWidth, bandWidth)
    return (int(sumPixel[0] / pixelCount), int(sumPixel[1] / pixelCount), int(sumPixel[2] / pixelCount))


def determineDominantColor(im):
    (width, height) = im.size
    colorCounter = {}
    for i in range(0, width, int(width / 100)):
        for j in range(0, height, int(height / 100)):
            color = im.getpixel((i, j))
            if color in colorCounter:
                colorCounter[color] = colorCounter[color] + 1
            else:
                colorCounter[color] = 1
                sortedCounter = sorted(iter(colorCounter.items()), key=operator.itemgetter(1))
    return sortedCounter[-1][0]


def getEuclideanDistance(a, b):
    return pow(a[0] - b[0], 2) + pow(a[1] - b[1], 2) + pow(a[2] - b[2], 2)


def getColorDistance(colorA, colorB, isFuzzy):
    #print "getColorDistance, a=", colorA, ", b=", colorB
    colorWhite = (255, 255, 255)
    colorBlack = (0, 0, 0)
    if colorB == (-1, -1, -1):
        shadeOfColorA = (colorA[1] + colorA[1] + colorA[2]) / 3
        if shadeOfColorA < 128:
            colorB = colorBlack
        else:
            colorB = colorWhite
    distance = getEuclideanDistance(colorA, colorB)
    if isFuzzy == True:
        distanceWhite = getEuclideanDistance(colorA, colorWhite)
        distanceBlack = getEuclideanDistance(colorA, colorBlack)
        distance = min(distanceWhite, distanceBlack, distance)
    return distance


def checkHorizontalBand(im, x1, y1, bandWidth, bgcolor, margin, diffThreshold, isFuzzy):
    #print "checkHorizontalBand(%d, %d)" % (x1, y1)
    (width, height) = im.size
    for j in range(y1, y1 + bandWidth):
        if j >= height:
            return (False, j - y1 + 1)
        diffCount = 0
        for i in range(x1 + margin, x1 + width - margin):
            pixel = im.getpixel((i, j))
            #print (i, j), pixel
            # 배경색과 불일치할 때 색상이 크게 차이나지 않으면 무시함
            if bgcolor == (-1, -1, -1):
                # blackorwhite
                if pixel == (0, 0, 0) or pixel == (255, 255, 255):
                    isSame = 1
                else:
                    isSame = 0
            else:
                # specific color
                if pixel == bgcolor:
                    isSame = 1
                else:
                    isSame = 0
            if isSame == 0:
                if getColorDistance(pixel, bgcolor, isFuzzy) > 3.0:
                    diffCount += 1
                    #print "y1=%d, diffCount=%d, convertedThreshold=%f" % (y1, diffCount, (width - 2 * margin) * diffThreshold)
                    # threshold 미만으로 불일치가 존재하면 false 반환
                    if diffCount > (width - 2 * margin) * diffThreshold:
                        return (False, j - y1 + 1)
    return (True, 0)


def checkVerticalBand(im, x1, y1, bandWidth, bgcolor, margin, diffThreshold, isFuzzy):
    #print "checkVerticalBand(%d, %d)" % (x1, y1)
    (width, height) = im.size
    for i in range(x1, x1 + bandWidth):
        if i >= width:
            return (False, i - x1 + 1)
        diffCount = 0
        for j in range(y1 + margin, y1 + height - margin):
            pixel = im.getpixel((i, j))
            #print (i, j), pixel
            # 배경색과 불일치할 때 색상이 크게 차이나지 않으면 무시함
            if bgcolor == (-1, -1, -1):
                # blackorwhite
                if pixel == (0, 0, 0) or pixel == (255, 255, 255):
                    isSame = 1
                else:
                    isSame = 0
            else:
                # specific color
                if pixel == bgcolor:
                    isSame = 1
                else:
                    isSame = 0
            if isSame == 0:
                if getColorDistance(pixel, bgcolor, isFuzzy) > 3.0:
                    diffCount += 1
                    #print x1, diffCount
                    # threshold 미만으로 불일치가 존재하면 false 반환
                    if diffCount > (height - 2 * margin) * diffThreshold:
                        return (False, i - x1 + 1)
    return (True, 0)


def findBgcolorBand(im, bgcolor, orientation, bandWidth, x1, y1, margin, diffThreshold, isFuzzy):
    #print "findBgcolorBand(orientation=%s)" % orientation
    (width, height) = im.size
    if orientation == "vertical":
        # 세로 이미지인 경우
        i = 0
        while y1 + i < height:
            # 가로 띠가 배경색으로만 구성되었는지 확인
            (flag, offset) = checkHorizontalBand(im, x1, y1 + i, bandWidth, bgcolor, margin, diffThreshold, isFuzzy)
            if flag:
                return (x1, int(y1 + i + bandWidth / 2))
            i += offset
    elif orientation == "horizontal":
        # 가로 이미지인 경우
        i = 0
        while x1 + i < width:
            # 세로 띠가 배경색으로만 구성되었는지 확인
            (flag, offset) = checkVerticalBand(im, x1 + i, y1, bandWidth, bgcolor, margin, diffThreshold, isFuzzy)
            if flag:
                return (int(x1 + i + bandWidth / 2), y1)
            i += offset
    return (-1, -1)


def determineColorOption(a):
    bgcolor = False
    doUseDominantColor = False
    isFuzzy = False
    if a == "white":
        bgcolor = (255, 255, 255)
    elif a == "black":
        bgcolor = (0, 0, 0)
    elif a == "blackorwhite":
        bgcolor = (-1, -1, -1)
    elif a == "dominant":
        doUseDominantColor = True
    elif a == "fuzzy":
        isFuzzy = True
        doUseDominantColor = True
    elif a[0] == "#":
        colorValue = int(a[1:], 16)
        bgcolor = (int(colorValue / 65536), int((colorValue % 65536) / 256), int(colorValue % 256))
    else:
        return False
    return (bgcolor, isFuzzy, doUseDominantColor)


def checkProportionAndUniformity(im):
    (width, height) = im.size
    stat = ImageStat.Stat(im)
    print("%f %f %f" % ((width/height), (height/width), max(stat.stddev)))
    if (width / height < 0.01 or height / width < 0.01) and max(stat.stddev) < 1:
        return False
    return True


def printUsage():
    print("Usage: %s [-r] -n #unit [-b bandwidth] [-m margin] [-c bgcolor] [-t threshold] [-v] [-i] imagefile" % (sys.argv[0]))
    print("\t-r: remove bouding box")
    print("\t-n #unit: more than 2")
    print("\t-b bandwidth (default %d)" % (defaultBandWith))
    print("\t-m margin (default %d)" % (defaultMargin))
    print("\t-c bgcolor: 'white' or 'black', 'blackorwhite', 'dominant', 'fuzzy', '#135fd8', ...")
    print("\t\tblackorwhite: black or white")
    print("\t\tdominant: most dominant color (automatic)")
    print("\t\tfuzzy: either black, white or prevailing color (automatic)")
    print("\t-t threshold: diff threshold (default %f)" % (defaultDiffThreshold))
    print("\t-v: split vertically")
    print("\t-i: ignore too thin and uniform slice (without saving)")
    
            
def main():
    # 옵션 처리
    bandWidth = defaultBandWith
    numUnits = defaultNumUnits
    margin = defaultMargin
    diffThreshold = defaultDiffThreshold;
    bgcolor = None
    doUseDominantColor = False
    isFuzzy = False
    doSplitVertically = False
    doIgnoreTooThinAndUniformSlice = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hb:n:m:c:rt:vi")
    except getopt.GetoptError as err:
        printUsage()
        sys.stderr.write("Error: Invaild option definition\n")
        sys.exit(-1)
    for o, a in opts:
        if o == "-b":
            bandWidth = int(a)
        elif o == "-m":
            margin = int(a)
        elif o == "-n":
            numUnits = int(a)
            if numUnits < 2:
                printUsage()
                sys.stderr.write("Error: n must be more than 1\n")
                sys.exit(-1)
        elif o == "-c":
            colorOption = determineColorOption(a)
            if colorOption == False:
                printUsage();
                sys.exit(-1)
            (bgcolor, isFuzzy, doUseDominantColor) = colorOption
        elif o == "-t":
            diffThreshold = float(a)
        elif o == "-v":
            doSplitVertically = True
        elif o == "-i":
            doIgnoreTooThinAndUniformSlice = True
        else:
            printUsage()
            sys.exit(-1)
    if len(args) < 1:
        printUsage()
        sys.stderr.write("Error: The image file is not specified\n")
        sys.exit(-1)
    imageFile = args[0]
    (namePrefix, ext) = os.path.splitext(imageFile)
    print("bandWidth=", bandWidth)
    print("numUnits=", numUnits)
    print("margin=", margin)
    print("diffThreshold=", diffThreshold)
    print("arg=", args[0])

    im = Image.open(imageFile)
    if im.mode != "RGB":
        im = im.convert("RGB")
    (width, height) = im.size
    print("width=%d, height=%d" % (width, height))
    if width > height or doSplitVertically:
        orientation = "horizontal"
    else:
        orientation = "vertical"
    print("orientation=", orientation)
    if orientation == "horizontal":
        unitWidth = int((width - bandWidth * (numUnits - 1)) / numUnits)
    else:
        unitWidth = int((height - bandWidth * (numUnits - 1)) / numUnits)
    print("unitWidth=", unitWidth)
    if doUseDominantColor == True:
        bgcolor = determineDominantColor(im)
    if bgcolor == None:
        bgcolor = determineBgcolor(im, 10)
    print("bgcolor=", bgcolor)
        
    (x0, y0) = (0, 0)
    if numUnits > 1:
        for i in range(0, numUnits):
            print("i=%d, numUnits=%d" % (i, numUnits))
            if orientation == "horizontal":
                #(x1, y1) = (((i + 1) * width - bandWidth * (numUnits - 1)) / numUnits, y0)
                (x1, y1) = (int(max((unitWidth + bandWidth) * (i + 1), x0 + unitWidth)), y0)
            else:
                #(x1, y1) = (x0, ((i + 1) * height - bandWidth * (numUnits - 1)) / numUnits)
                (x1, y1) = (x0, int(max((unitWidth + bandWidth) * (i + 1), y0 + unitWidth)))
            print("(x0, y0)=", (x0, y0))
            print("(x1, y1)=", (x1, y1))
            if x0 >= width - bandWidth or y0 >= height - bandWidth or x1 >= width - bandWidth or y1 >= height - bandWidth:
                break
            # 배경색으로만 구성된 띠를 찾아냄
            (x1, y1) = findBgcolorBand(im, bgcolor, orientation, bandWidth, x1, y1, margin, diffThreshold, isFuzzy)
            print("cutting point=", (x1, y1))
            if (x1, y1) == (-1, -1):
                sys.stderr.write("Error: no splitting\n")
                break
            # 잘라서 저장
            if orientation == "horizontal":
                print("crop: x0=%d, y0=%d, x1=%d, height=%d" % (x0, y0, x1, height))
                subIm = im.crop((x0, y0, x1, height))
            else:
                print("crop: x0=%d, y0=%d, width=%d, y1=%d" % (x0, y0, width, y1))
                subIm = im.crop((x0, y0, width, y1))

            if doIgnoreTooThinAndUniformSlice:
                doSave = checkProportionAndUniformity(subIm)
            else:
                doSave = True
            if doSave:
                try:
                    subIm.save(namePrefix + "." + str(i + 1) + ext, quality=defaultQuality)
                except SystemError:
                    sys.stderr.write("Error: can't save the split image\n");
                    raise
                #(x0, y0) = (x1, y1)
                if orientation == "horizontal":
                    (x0, y0) = (x1, y1)
                else:
                    (x0, y0) = (x1, y1)
                print()

        # 나머지 부분 저장
        print("last cutting point=", (width, height))
        subIm = im.crop((x0, y0, width, height))
        if doIgnoreTooThinAndUniformSlice:
            doSave = checkProportionAndUniformity(subIm)
        else:
            doSave = True
        if doSave:
            subIm.save(namePrefix + "." + str(i + 1) + ext, quality=defaultQuality)

        
if __name__ == "__main__":
    main()
