#!/bin/bash 
#
# Author: Izidor Matušov <izidor.matusov@gmail.com>
# Date:   27.07.2011

deploy() {
    prefix="$1"
    shift

for file
do
    # Skip watchdog => it is in a different place
    if [ "$file" = "tests/watchdog.py" ] ; then
        continue
    fi

    lib_file="$prefix/$file"
    cp -v "$file" "$lib_file"

    # Beware! Order of those lines is important!
    sed  \
        -e 's#^from liblarch_gtk#from GTG.gtk.liblarch_gtk#' \
        -e 's#^from liblarch#from GTG.tools.liblarch#' \
        -e 's#^from tests\.watchdog#from GTG.tools.watchdog#' \
        -e 's#^from tests\.#from GTG.tests.#' \
        -e 's#^TEST_MODULE_PREFIX = .*#TEST_MODULE_PREFIX = "GTG.tests."#' \
        -i "$lib_file"
done
}

# Go to its directory
cd $(dirname $0)

make clean
deploy ../integrate-liblarch-to-gtg/GTG/tools/ liblarch/*
deploy ../integrate-liblarch-to-gtg/GTG/gtk/ liblarch_gtk/*
deploy ../integrate-liblarch-to-gtg/GTG/ tests/*
