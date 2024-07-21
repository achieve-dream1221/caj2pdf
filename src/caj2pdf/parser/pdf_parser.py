#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/19 下午3:05
# @Author  : ACHIEVE_DREAM
# @File    : pdf_parser.py
# @Software: Pycharm
import shutil
from pathlib import Path
from loguru import logger


def pdf_parser(src: Path, dest: Path) -> None:
    logger.debug(f"{src.name} is %PDF format")
    shutil.copy(src, dest)
