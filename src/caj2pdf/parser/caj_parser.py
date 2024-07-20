#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/20 下午1:02
# @Author  : ACHIEVE_DREAM
# @File    : caj_parser.py
# @Software: Pycharm
import io
import os
import re
import subprocess
from pathlib import Path

from ..utils import CajOffset, to_int32


def caj_parser(src: Path, dest: Path, offset: CajOffset):
    with src.open("rb") as fp:
        data = fp.read()
    pdf_start = to_int32(data, to_int32(data, offset.page_num + 4))
    pdf_end = data.rfind(b"endobj") + 6
    pdf_data = b"%PDF-1.3\r\n" + data[pdf_start:pdf_end] + b"\r\n"
    page_num = to_int32(data, offset.page_num) if offset.page_num != 0 else 0
    end_obj_addr = find_all(pdf_data, b"endobj")
    obj_no = set()
    for addr in end_obj_addr:
        start_obj = pdf_data[:addr].rfind(b" 0 obj") + 6
        start_obj = max(pdf_data[:start_obj].rfind(b"\r") + 1, pdf_data[:start_obj].rfind(b"\n") + 1)
        end_obj = pdf_data.find(b" ", start_obj)
        no = int(pdf_data[start_obj:end_obj])
        obj_no.add(no)

    ind_set = set()
    for addr in find_all(pdf_data, b"/Parent "):
        addr += 8
        end = pdf_data.find(b" ", addr)
        ind_set.add(int(pdf_data[addr:end]))

    pages_obj_no = set()
    top_pages_obj_no = set()
    for ind in ind_set:
        if pdf_data.find(bytes(f"\r{ind} 0 obj", 'utf8')) == -1:
            top_pages_obj_no.add(ind)
        else:
            pages_obj_no.add(ind)
    single_pages_obj_missed = len(top_pages_obj_no) == 1
    multi_pages_obj_missed = len(top_pages_obj_no) > 1
    # generate catalog object: 生成目录对象
    catalog_obj_no = obj_no.pop()
    obj_no.add(catalog_obj_no)
    root_pages_obj_no = None
    if multi_pages_obj_missed:
        root_pages_obj_no = catalog_obj_no + 1
    elif single_pages_obj_missed:
        root_pages_obj_no = top_pages_obj_no.pop()
        top_pages_obj_no = pages_obj_no
    else:  # root pages object exists, then find the root pages object #
        found = False
        for pon in pages_obj_no:
            search_bytes = bytes(f"\r{pon} 0 obj", 'utf8')
            tmp_addr = pdf_data.find(search_bytes) + len(search_bytes)
            while (_str := pdf_data[tmp_addr:tmp_addr + 6]) != b"Parent":
                if _str == b"endobj":
                    root_pages_obj_no = pon
                    found = True
                    break
                tmp_addr += 1
            if found:
                break
    catalog = bytes(
        f"{catalog_obj_no} 0 obj\r<</Type /Catalog\r/Pages {root_pages_obj_no} 0 R\r>>\rendobj\r", "utf-8")
    pdf_data += catalog
    pdf = io.BytesIO(pdf_data)
    # Add Pages obj and EOF mark if root pages object exist, pass deal with single missing pages object
    # 如果根页面对象存在，则添加页面 obj 和 EOF 标记，传递处理单个缺失页面对象
    if single_pages_obj_missed or multi_pages_obj_missed:
        inds_str = [f"{i} 0 R" for i in top_pages_obj_no]
        kids_str = f"[{" ".join(inds_str)}]"
        pages_str = f"{root_pages_obj_no} 0 obj\r<<\r/Type /Pages\r/Kids {kids_str}\r/Count {page_num}\r>>\rendobj\r"
        pdf_data += bytes(pages_str, "utf-8")
        pdf = io.BytesIO(pdf_data)
    # 处理多个缺失的 Pages 对象
    if multi_pages_obj_missed:
        kids_dict = {i: set() for i in top_pages_obj_no}
        count_dict = {i: 0 for i in top_pages_obj_no}
        for tpon in top_pages_obj_no:
            for kid in find_all(pdf_data, bytes(f"/Parent {tpon} 0 R", "utf-8")):
                ind = pdf_data[:kid].rfind(b" obj")
                addr = pdf_data[:ind].rfind(b"\r") + 1
                end_obj = pdf_data.find(b" ", addr)
                kids_dict[tpon].add(int(pdf_data[addr:end_obj]))
                tmp_addr = pdf_data.find(b"/", pdf_data.find(b"/Type", addr) + 5) + 1
                if pdf_data[tmp_addr:tmp_addr + 5] == b"Pages":
                    cnt_addr = pdf_data.find(b"/Count ", addr) + 7
                    cnt_len = 0
                    while pdf_data[cnt_addr:cnt_addr + 1] not in [b" ", b"\r", b"/"]:
                        cnt_len += 1
                        cnt_addr += 1
                    cnt = int(pdf_data[cnt_addr - cnt_len: cnt_addr])
                    count_dict[tpon] += cnt
                else:  # _type == b"Page"
                    count_dict[tpon] += 1
            kids_no_str = [f"{i} 0 R" for i in kids_dict[tpon]]
            kids_str = f"[{" ".join(kids_no_str)}]"
            pages_str = f"{tpon} 0 obj\r<<\r/Type /Pages\r/Kids {kids_str}\r/Count {count_dict[tpon]}\r>>\rendobj\r"
            pdf_data += bytes(pages_str, "utf-8")
    pdf_data += bytes("\n%%EOF\r", "utf-8")
    tmp = dest.with_suffix(".tmp")
    with tmp.open("wb") as fp:
        fp.write(pdf_data)
    subprocess.run(["pymupdf", "clean", tmp, dest])
    os.remove(tmp)


def find_all(data: bytes, search_bytes: bytes) -> list[int]:
    """
    从data中找出所有搜索字节串的位置
    :param data: 字节数组
    :param search_bytes: 搜索字节
    :return: 位置列表
    """
    pattern = re.compile(search_bytes)
    return [matched.start() for matched in pattern.finditer(data)]
