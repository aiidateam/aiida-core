#!/bin/bash
fldr=source/apidoc

rm -rf build $fldr

mkdir $fldr
sphinx-apidoc -o $fldr ../aiida \
    --separate \
    --private

make html
