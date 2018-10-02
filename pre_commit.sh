#!/bin/bash

PYS=$(find . -name '*.py')
python3-autopep8 -i ${PYS}
python3-flake8 ${PYS}

SHS=$(find . -name '*.sh')
txtnet ${SHS}
