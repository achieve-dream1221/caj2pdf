#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/18 下午8:15
# @Author  : ACHIEVE_DREAM
# @File    : utils.py
# @Software: Pycharm
import enum
from pathlib import Path


def to_int32(data: bytes, start: int) -> int:
    """
    从data字节流读取4个字节
    :param data: 字节数组
    :param start: 开始位置
    :return: 解析的数字
    """
    return int.from_bytes(data[start : start + 4], "little")


class CajFormat(enum.Enum):
    C8 = "C8"
    HN1 = "HN"
    HN2 = "HN2"
    PDF = "%PDF"
    CAJ = "CAJ"
    KDH = "KDH"
    TEB = "TEB"


def get_format(path: str | Path) -> CajFormat:
    """
    预处理文件
    :param path: caj文件路径
    :return: 文件对象, 文件元格式, 文件偏移量
    """
    if isinstance(path, str):
        path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    if not path.is_file():
        raise TypeError(f"{path} is not a file")
    with path.open("rb") as fp:
        read4 = fp.read(4)
        if read4[:1] == b"\xc8":
            fmt = CajFormat.C8
            # offset.page_num = 0x08
            # offset.toc_end = 0x50
            # offset.page_data = offset.toc_end + 20 * get_num(fp, offset.page_num)
        elif read4[:2] == b"HN" and fp.read(2) == b"\xc8\x00":
            fmt = CajFormat.HN1
            # offset.page_num = 0x90
            # offset.toc_end = 0xD8
            # offset.page_data = offset.toc_end + 20 * get_num(fp, offset.page_num)
        else:
            # 移除空字节, 字符串结束标志, 移除空格, 并解码为字符串 KDH CAJ HN %PDF
            match read4.replace(b"\x00", b"").replace(b"\x20", b"").decode():
                case "CAJ":
                    fmt = CajFormat.CAJ
                    # offset.page_num = 0x10
                    # offset.toc_num = 0x110
                case "HN":
                    fmt = CajFormat.HN2
                    # offset.page_num = 0x90
                    # offset.toc_num = 0x158
                    # offset.toc_end = (
                    #         offset.toc_num + 4 + 0x134 * get_num(fp, offset.toc_num)
                    # )
                    # offset.page_data = offset.toc_end + 20 * get_num(
                    #     fp, offset.page_num
                    # )
                case "%PDF":
                    fmt = CajFormat.PDF
                case "KDH":
                    fmt = CajFormat.KDH
                case "TEB":
                    fmt = CajFormat.TEB
                case _:
                    raise TypeError("unknown file type")
    return fmt
