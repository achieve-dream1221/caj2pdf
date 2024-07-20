#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/19 下午4:32
# @Author  : ACHIEVE_DREAM
# @File    : parser.py
# @Software: Pycharm
from ..utils import preprocess
from pathlib import Path
from loguru import logger
from .pdf_parser import pdf_parser
from .caj_parser import caj_parser


def convert(src: str, dest: str = None):
    src, fmt, offset = preprocess(src)
    if dest is None:
        dest = src.stem + ".pdf"
    dest = Path(dest)
    # 创建父级文件夹,若存在则不创建
    dest.parent.mkdir(parents=True, exist_ok=True)
    # resolve: 将路径转换为绝对路径
    logger.info(f"convert from {src.resolve()} to {dest.resolve()}")
    match fmt:
        case "PDF":
            pdf_parser(src, dest)
        case "CAJ":
            caj_parser(src, dest, offset)
        case other:
            logger.error(f"{other} format is not implemented!")
            return
    logger.debug("convert success!")
