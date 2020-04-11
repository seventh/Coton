#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools as st

st.setup(
    name="Coton",
    version="0.0",
    package_dir={"": "src"},
    packages=st.find_namespace_packages(where="src", exclude=["test."]),
    author="Guillaume Lemaître",
    url="https://github.com/seventh/Coton",
)
