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

echo "success"
rm -f temp.result vertical.*.jpg horizontal.*.jpg

