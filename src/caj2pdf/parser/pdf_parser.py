#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/19 下午3:05
# @Author  : ACHIEVE_DREAM
# @File    : pdf_parser.py
# @Software: Pycharm
import shutil
from pathlib import Path


def pdf_parser(src: Path, dest: Path):
    shutil.copy(src, dest)
