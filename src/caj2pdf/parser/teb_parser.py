#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/21 下午4:12
# @Author  : ACHIEVE_DREAM
# @File    : teb_parser.py
# @Software: Pycharm
from pathlib import Path


def teb_parser(src: str | Path, dest: str | Path) -> None:
    if isinstance(src, str):
        src = Path(src)
    if isinstance(dest, str):
        dest = Path(dest)
    raise NotImplementedError
