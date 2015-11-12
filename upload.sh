#!/bin/bash

## Globals
###################################################

RAD="shksystem.net"
VERS="0.1.8.2"

EGG_INFO="shk_${RAD}.egg-info"
GEMFURY_URL="https://pypi.fury.io/eFMwY1qjNYLsUZ-5Q6mF/sarfraz/"
WHEEL_FILE="${RAD}-${VERS}-py2.py3-none-any.whl"
ACTIVATE=env/bin/activate

## Functions
###################################################

function cleanup {
    cleanup_list=( dist build $1 )
    for ref in ${cleanup_list[@]}
    do
        rm -rf $ref
    done
}


## Main
###################################################

cleanup $EGG_INFO
source $ACTIVATE
python setup.py bdist_wheel
curl -F package=@dist/$WHEEL_FILE $GEMFURY_URL
cleanup $EGG_INFO

exit 0

