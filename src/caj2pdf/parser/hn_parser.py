#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/21 下午4:05
# @Author  : ACHIEVE_DREAM
# @File    : hn_parser.py
# @Software: Pycharm
from pathlib import Path


def hn1_parser(src: str | Path, dest: str | Path) -> None:
    if isinstance(src, str):
        src = Path(src)
    if isinstance(dest, str):
        dest = Path(dest)
    raise NotImplementedError


def hn2_parser(src: str | Path, dest: str | Path) -> None:
    if isinstance(src, str):
        src = Path(src)
    if isinstance(dest, str):
        dest = Path(dest)
    raise NotImplementedError
