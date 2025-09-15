#!/bin/sh

CRNT_DIR=$(cd $(dirname $0);pwd)
cd ${CRNT_DIR}/../src && sudo sam build --use-container && sam deploy $@