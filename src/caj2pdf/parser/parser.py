#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/19 下午4:32
# @Author  : ACHIEVE_DREAM
# @File    : parser.py
# @Software: Pycharm
from ..utils import get_format, CajFormat
from pathlib import Path
from loguru import logger
from .pdf_parser import pdf_parser
from .caj_parser import caj_parser
from .c8_parser import c8_parser
from .hn_parser import hn1_parser, hn2_parser
from .kdh_parser import kdh_parser
from .teb_parser import teb_parser
import time


def convert(src: str, dest: str = None) -> None:
    """
    caj文件转pdf
    :param src: 源文件路径
    :param dest: 保存路径, 默认为src目录下converted文件夹下
    :return: None
    """
    src = Path(src)
    fmt = get_format(src)
    if dest is None:
        # 如果没有设置目标存储目录,则在源文件同级目录下创建converted目录
        dest = src.parent / "converted" / (src.stem + ".pdf")
    dest = Path(dest)
    # 创建父级文件夹,若存在则不创建
    dest.parent.mkdir(parents=True, exist_ok=True)
    # resolve: 将路径转换为绝对路径
    logger.info(f"convert from {src.resolve()} to {dest.resolve()}")
    start = time.perf_counter()
    match fmt:
        case CajFormat.PDF:
            pdf_parser(src, dest)
        case CajFormat.CAJ:
            caj_parser(src, dest)
        # case CajFormat.C8:
        #     c8_parser(src, dest)
        # case CajFormat.HN1:
        #     hn1_parser(src, dest)
        # case CajFormat.HN2:
        #     hn2_parser(src, dest)
        # case CajFormat.KDH:
        #     kdh_parser(src, dest)
        # case CajFormat.TEB:
        #     teb_parser(src, dest)
        case other:
            logger.error(f"{other.value} format is not implemented!")
            return
    logger.info(f"总耗时: {time.perf_counter() - start:.5f} s")
    logger.success("convert success!")
