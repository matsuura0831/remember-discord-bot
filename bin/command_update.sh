#!/bin/sh

CRNT_DIR=$(cd $(dirname $0);pwd)
cd ${CRNT_DIR}/../src/tools && pip install -r requirements.txt && python register_command.py