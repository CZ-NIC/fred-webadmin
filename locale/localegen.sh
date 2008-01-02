#!/bin/bash

for file in `ls -1 *.po`; do
    f=`echo $file | cut -d . -f 1`
    msgfmt $file -o $f/LC_MESSAGES/adif.mo
done
