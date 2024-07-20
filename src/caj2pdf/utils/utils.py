#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/18 下午8:15
# @Author  : ACHIEVE_DREAM
# @File    : utils.py
# @Software: Pycharm

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


@dataclass
class CajOffset:
    """Caj偏移量"""
    page_num: int
    toc_num: int
    toc_end: int
    page_data: int


def get_num(fp: BinaryIO, number_offset: int) -> int:
    """
    获取数量
    :param fp: 文件对象或者二进制流对象
    :param number_offset: 数字偏移量
    :return: 解析数字
    """
    if number_offset == 0:
        return 0
    fp.seek(number_offset)
    return read_int32(fp)


def read_int32(fp: BinaryIO) -> int:
    """
    根据字节流读取4个字节32的数字
    :param fp: 流对象
    :param start: 开始位置
    :return: 解析的数字
    """
    # fp.seek(start)
    return int.from_bytes(fp.read(4), "little")


def to_int32(data: bytes, start: int) -> int:
    """
    从data字节流读取4个字节
    :param data: 字节数组
    :param start: 开始位置
    :return: 解析的数字
    """
    return int.from_bytes(data[start:start + 4], "little")


def preprocess(path: str) -> tuple[Path, str, CajOffset]:
    """
    预处理文件
    :param path: caj文件路径
    :return: 文件对象, 文件元格式, 文件偏移量
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"{path} not found")
    if not p.is_file():
        raise TypeError(f"{path} is not a file")
    offset = CajOffset(0, 0, 0, 0)
    with p.open("rb") as fp:
        read4 = fp.read(4)
        if read4[:1] == b"\xc8":
            fmt = "C8"
            offset.page_num = 0x08
            offset.toc_end = 0x50
            offset.page_data = offset.toc_end + 20 * get_num(fp, offset.page_num)
        elif read4[:2] == b"HN" and fp.read(2) == b"\xc8\x00":
            fmt = "HN"
            offset.page_num = 0x90
            offset.toc_end = 0xD8
            offset.page_data = offset.toc_end + 20 * get_num(fp, offset.page_num)
        else:
            # 移除空字节, 字符串结束标志, 移除空格, 移除%, 并解码为字符串 KDH CAJ HN %PDF
            fmt = read4.replace(b"\x00", b"").replace(b"\x20", b"").replace(b"\x25", b"").decode()
            match fmt:
                case "CAJ":
                    offset.page_num = 0x10
                    offset.toc_num = 0x110
                case "HN":
                    offset.page_num = 0x90
                    offset.toc_num = 0x158
                    offset.toc_end = offset.toc_num + 4 + 0x134 * get_num(fp, offset.toc_num)
                    offset.page_data = offset.toc_end + 20 * get_num(fp, offset.page_num)
                case "PDF" | "KDH" | "TEB":
                    pass
                case _:
                    raise TypeError("unknown file type")
    return p, fmt, offset
