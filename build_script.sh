#!/usr/bin/env bash

run_tests() {
    apt-get update -qy &&
    apt-get install -y python3-dev python3-pip &&
    pip3 install -r requirements.txt &&
    python3.5 -c "if not hasattr(__import__('sys'), 'real_prefix'): print('WARNING: tests running outside virtualenv')" &&
    nosetests --with-coverage --cover-package=aschedule --cover-min-percentage=90 --cover-config-file=.coveragerc --processes=50 --process-timeout=600 --cover-inclusive
    return $?
}

install() {
    apt-get update -qy &&
    apt-get install -y python3-dev python3-pip &&
    python3.5 setup.py install
    return $?
}

build_pages() {
    apt-get update -qy &&
    apt-get install -y python3-dev python3-pip &&
    pip3 install -r requirements.txt &&
    make -C docs html &&
    mkdir public &&
    cp -rv docs/build/html/* public/
    return $?
}

date
"$@"
exit_code=$?
date

exit $exit_code
