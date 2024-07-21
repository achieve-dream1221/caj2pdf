#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/20 下午1:02
# @Author  : ACHIEVE_DREAM
# @File    : caj_parser.py
# @Software: Pycharm
import re
import subprocess
from pathlib import Path
from loguru import logger
import time

from ..utils import to_int32


def caj_parser(src: str | Path, dest: str | Path) -> None:
    if isinstance(src, str):
        src = Path(src)
    if isinstance(dest, str):
        dest = Path(dest)
    logger.debug(f"{src.name} is CAJ format!")
    with src.open("rb") as fp:  # 读取原始caj二进制内容
        content = fp.read()
    # 目录暂未使用: toc_num_offset=0x110
    page_num_offset = 0x10
    pdf_start = to_int32(content, to_int32(content, page_num_offset + 4))
    pdf_end = content.rfind(b"endobj") + 6
    content = b"%PDF-1.3\r\n" + content[pdf_start:pdf_end] + b"\r\n"
    page_num = to_int32(content, page_num_offset)
    obj_numbers = set()
    for addr in find_all(content, b"endobj"):
        start = content.rfind(b" 0 obj", 0, addr) + 6
        start = max(
            content.rfind(b"\r", 0, start), content.rfind(b"\n", 0, start) + 1
        ) + 1
        obj_numbers.add(int(content[start:content.find(b" ", start)]))
    # 性能测试专用
    # start = time.perf_counter()
    # logger.debug(f"耗时: {time.perf_counter() - start:.5f} s")
    ind_set = {int(content[i + 8:content.find(b" ", i + 8)]) for i in find_all(content, b"/Parent ")}
    pattern = re.compile(bytes(r"\r(\d+) 0 obj", "utf8"))
    pages_obj_numbers = {int(i) for i in set(pattern.findall(content))}.intersection(ind_set)  # 取交集
    top_pages_obj_numbers = ind_set.difference(pages_obj_numbers)  # 取差集

    single_pages_obj_missed = len(top_pages_obj_numbers) == 1
    multi_pages_obj_missed = len(top_pages_obj_numbers) > 1
    catalog_obj_number = max(obj_numbers) + 1
    obj_numbers.add(catalog_obj_number)

    root_pages_obj_number = None
    if multi_pages_obj_missed:
        root_pages_obj_number = catalog_obj_number + 1
    elif single_pages_obj_missed:
        root_pages_obj_number = min(top_pages_obj_numbers)
        top_pages_obj_numbers = pages_obj_numbers
    else:  # root pages object exists, then find the root pages object #
        found = False  # TODO: 待优化
        for pon in pages_obj_numbers:
            search_bytes = bytes(f"\r{pon} 0 obj", "utf8")
            tmp_addr = content.find(search_bytes) + len(search_bytes)
            while (_str := content[tmp_addr: tmp_addr + 6]) != b"Parent":
                if _str == b"endobj":
                    root_pages_obj_number = pon
                    found = True
                    break
                tmp_addr += 1
            if found:
                break

    content += bytes(
        f"{catalog_obj_number} 0 obj\r<</Type /Catalog\r/Pages {root_pages_obj_number} 0 R\r>>\rendobj\r",
        "utf-8",
    )
    # Add Pages obj and EOF mark if root pages object exist, pass deal with single missing pages object
    # 如果根页面对象存在，则添加页面 obj 和 EOF 标记，传递处理单个缺失页面对象
    if single_pages_obj_missed or multi_pages_obj_missed:
        kids_str = f"[{" ".join([f"{i} 0 R" for i in top_pages_obj_numbers])}]"
        pages_str = f"{root_pages_obj_number} 0 obj\r<<\r/Type /Pages\r/Kids {kids_str}\r/Count {page_num}\r>>\rendobj\r"
        content += bytes(pages_str, "utf-8")
    # 处理多个缺失的 Pages 对象
    start = time.perf_counter()
    if multi_pages_obj_missed:
        for number in top_pages_obj_numbers:
            kids = []
            count = 0
            for kid in find_all(content, bytes(f"/Parent {number} 0 R", "utf-8")):
                start_addr = content.rfind(b"\r", 0, content.rfind(b"\r", 0, kid)) + 1
                end_addr = content.find(b" ", start_addr)
                kids.append(int(content[start_addr:end_addr]))
                tmp_addr = content.find(b"/", content.find(b"/Type", start_addr) + 5) + 1
                if content[tmp_addr: tmp_addr + 5] == b"Pages":
                    count_addr = content.find(b"/Count ", start_addr) + 7
                    count_len = 0
                    while content[count_addr: count_addr + 1] not in [b" ", b"\r", b"/"]:
                        count_len += 1
                        count_addr += 1
                    count += int(content[count_addr - count_len: count_addr])
                else:  # _type == b"Page"
                    count += 1
            kids_str = f"[{" ".join([f"{i} 0 R" for i in kids])}]"
            pages_str = bytes(f"{number} 0 obj\r<<\r/Type /Pages\r/Kids {kids_str}\r/Count {count}\r>>\rendobj\r",
                              "utf8")
            content += pages_str
    logger.debug(f"耗时: {time.perf_counter() - start:.5f} s")
    content += bytes("\n%%EOF\r", "utf-8")
    tmp = dest.with_suffix(".tmp")
    with tmp.open("wb") as fp:
        fp.write(content)
    subprocess.run(["pymupdf", "clean", tmp, dest])
    tmp.unlink(missing_ok=True)


def find_all(data: bytes, search_bytes: bytes) -> list[int]:
    """
    从data中找出所有搜索字节串的位置
    :param data: 字节数组
    :param search_bytes: 搜索字节
    :return: 位置列表生成器
    """
    pattern = re.compile(search_bytes)
    for matched in pattern.finditer(data):
        yield matched.start()
