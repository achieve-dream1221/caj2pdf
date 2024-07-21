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


def convert(src: str, dest: str = None) -> None:
    """
    caj文件转pdf
    :param src: 源文件路径
    :param dest: 保存路径
    :return: None
    """
    src, fmt, offset = preprocess(src)
    if dest is None:
        # 如果没有设置目标存储目录,则在源文件同级目录下创建converted目录
        dest = src.parent / "converted" / (src.stem + ".pdf")
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
    logger.success("convert success!")
