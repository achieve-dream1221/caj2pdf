#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/19 下午3:05
# @Author  : ACHIEVE_DREAM
# @File    : pdf_parser.py
# @Software: Pycharm
import shutil
from pathlib import Path
from loguru import logger


def pdf_parser(src: str | Path, dest: str | Path) -> None:
    """
    pdf转换
    :param src: 源路径
    :param dest: 目标路径
    :return: None
    """
    if isinstance(src, str):
        src = Path(src)
    logger.debug(f"{src.name} is %PDF format!")
    shutil.copy(src, dest)
