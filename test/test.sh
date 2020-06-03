#!/bin/bash

../split.py -n 5 vertical.jpg > temp.result
diff temp.result n5.v.result > /dev/null 2>&1 || (echo "n5.v failure"; exit -1)
../split.py -n 4 vertical.jpg > temp.result
diff temp.result n4.v.result > /dev/null 2>&1 || (echo "n4.v failure"; exit -1)
../split.py -n 3 vertical.jpg > temp.result
diff temp.result n3.v.result > /dev/null 2>&1 || (echo "n3.v failure"; exit -1)
../split.py -n 2 vertical.jpg > temp.result
diff temp.result n2.v.result > /dev/null 2>&1 || (echo "n2.v failure"; exit -1)

../split.py -n 5 horizontal.jpg > temp.result
diff temp.result n5.h.result > /dev/null 2>&1 || (echo "n5.h failure"; exit -1)
../split.py -n 4 horizontal.jpg > temp.result
diff temp.result n4.h.result > /dev/null 2>&1 || (echo "n4.h failure"; exit -1)
../split.py -n 3 horizontal.jpg > temp.result
diff temp.result n3.h.result > /dev/null 2>&1 || (echo "n3.h failure"; exit -1)
../split.py -n 2 horizontal.jpg > temp.result
diff temp.result n2.h.result > /dev/null 2>&1 || (echo "n2.h failure"; exit -1)

../split.py -n 25 -b 10 -c blackorwhite vertical2.jpg > temp.result
diff temp.result n25.v2bw.result > /dev/null 2>&1 || (echo "n25.v2bw failure"; exit -1)

../split.py -n 10 -c dominant vertical.jpg > temp.result
diff temp.result n10.vd.result > /dev/null 2>&1 || (echo "n10.vd failure"; exit -1)

../split.py -n 10 -c fuzzy vertical.jpg > temp.result
diff temp.result n10.vf.result > /dev/null 2>&1 || (echo "n10.vf failure"; exit -1)

../split.py -n 25 -b 10 -c fuzzy vertical2.jpg > temp.result
diff temp.result n25.v2f.result > /dev/null 2>&1 || (echo "n25.v2f failure"; exit -1)

../split.py -n 25 -c fuzzy vertical3.jpg > temp.result
diff temp.result n25.v3f.result > /dev/null 2>&1 || (echo "n25.v3f failure"; exit -1)

../split.py -n 25 -c fuzzy vertical4.jpg > temp.result
diff temp.result n25.v4f.result > /dev/null 2>&1 || (echo "n25.v4f failure"; exit -1)

# 첫번째 슬라이스가 너무 얇아서 쪼개지지 않는 케이스
../split.py -n 2 -b 10 vertical5.jpg > temp.result
diff temp.result n2.v5.result > /dev/null 2>&1 || (echo "n2.v5bw failure"; exit -1)

# 마지막 슬라이스가 너무 얇아서 이전 이미지에 붙여서 같은 이름으로 다시 저장해야 하는 케이스
../split.py -n 2 -b 0 -t 1.0 -v -c blackorwhite horizontal3.jpg > temp.result
diff temp.result n2.h3.result > /dev/null 2>&1 || (echo "n2.h3bw failure"; exit -1)

../split.py -n 3 -b 10 vertical6.jpg > temp.result
diff temp.result n3.v6.result > /dev/null 2>&1 || (echo "n3.v2bw failure"; exit -1)

echo "success"
rm -f temp.result vertical*.*.jpg horizontal*.*.jpg
