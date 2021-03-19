#!/bin/bash


function clean_temp_files {
    rm -f temp.result vertical*.*.jpg horizontal*.*.jpg
}

function run_test {
    test_case_name=""
    for arg in "$@"; do
        new_arg=$(printf "%s" "$arg" | sed -e 's/^\-//')
        new_arg=$(printf "%s" "$new_arg" | sed -e 's/\.jpg$//')
        if [[ $test_case_name == "" ]]; then
            test_case_name="$new_arg"
        else
            test_case_name="${test_case_name}_${new_arg}"
        fi
    done

    ../split.py "$@" > ${test_case_name}.result
    diff ${test_case_name}.expected ${test_case_name}.result > /dev/null 2>&1
    if [[ $? != 0 ]]; then
        echo "failure in $test_case_name"
        echo "diff ${test_case_name}.expected ${test_case_name}.result"
        clean_temp_files
        exit -1
    fi
}

run_test -n 5 vertical.jpg
run_test -n 4 vertical.jpg
run_test -n 3 vertical.jpg
run_test -n 2 vertical.jpg
run_test -n 10 -c dominant vertical.jpg
run_test -n 10 -c fuzzy vertical.jpg

run_test -n 25 -b 10 -c blackorwhite vertical2.jpg
run_test -n 25 -b 10 -c fuzzy vertical2.jpg

run_test -n 25 -c fuzzy vertical3.jpg

run_test -n 25 -c fuzzy vertical4.jpg

# 첫번째 슬라이스가 너무 얇아서 쪼개지지 않는 케이스
run_test -n 2 -b 10 vertical5.jpg

run_test -n 3 -b 10 vertical6.jpg

run_test -n 5 horizontal.jpg
run_test -n 4 horizontal.jpg
run_test -n 3 horizontal.jpg
run_test -n 2 horizontal.jpg

run_test -n 3 horizontal2.jpg

# 마지막 슬라이스가 너무 얇아서 이전 이미지에 붙여서 같은 이름으로 다시 저장해야 하는 케이스
run_test -n 2 -b 0 -t 1.0 -v -c blackorwhite horizontal3.jpg

clean_temp_files

echo success
