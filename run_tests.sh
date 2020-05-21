#!/bin/bash
if [ $# -eq 2 ]
  then
    export CYVERSE_USERNAME=$1
    export CYVERSE_PASSWORD=$2
else
  echo "Warning: Cyverse Downloader tests will fail if username/password not supplied"
  echo "example: ./run_tests.sh <cyverse_username> <cyverse_password>"
fi
python -m unittest discover test -p '*_tests.py'
