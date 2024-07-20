#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/20 下午1:02
# @Author  : ACHIEVE_DREAM
# @File    : caj_parser.py
# @Software: Pycharm
import io
import os
import re
import struct
import sys
from pathlib import Path
from subprocess import STDOUT, CalledProcessError, check_output
from typing import BinaryIO

from pypdf.generic import (
    NameObject,
    ArrayObject,
    NullObject,
)

from ..utils import CajOffset, get_num, read_int32, to_int32


def caj_parser(src: Path, dest: Path, offset: CajOffset):
    with src.open("rb") as fp:
        data = fp.read()
    start = offset.page_num + 4
    start = to_int32(data, start)
    pdf_start = to_int32(data, start)
    pdf_end = data.rfind(b"endobj") + 6
    # pdf_end = find_all(fp, b"endobj")[-1] + 6
    pdf_length = pdf_end - pdf_start
    pdf_data = b"%PDF-1.3\r\n" + data[pdf_start:pdf_start+pdf_length] + b"\r\n"
    pdf = io.BytesIO(pdf_data)
    page_num = get_num(fp, offset.page_num)
    end_obj_addr = find_all(pdf.read(), b"endobj")
    obj_no = []
    for addr in end_obj_addr:
        startobj = fnd_rvrs(pdf, b" 0 obj", addr)
        startobj1 = fnd_rvrs(pdf, b"\r", startobj)
        startobj2 = fnd_rvrs(pdf, b"\n", startobj)
        startobj = max(startobj1, startobj2)
        length = find(pdf, b" ", startobj) - startobj
        pdf.seek(startobj)
        [no] = struct.unpack(str(length) + "s", pdf.read(length))
        # no = pdf.read(length).decode()
        if int(no) not in obj_no:
            obj_no.append(int(no))
            # obj_len = addr - startobj + 6
            pdf.seek(startobj)
            # [obj] = struct.unpack(str(obj_len) + "s", pdf.read(obj_len))
    inds_addr = [i + 8 for i in find_all(pdf, b"/Parent")]
    inds = []
    for addr in inds_addr:
        length = find(pdf, b" ", addr) - addr
        pdf.seek(addr)
        [ind] = struct.unpack(str(length) + "s", pdf.read(length))
        inds.append(int(ind))
    # get pages_obj_no list containing distinct elements
    # & find missing pages object(s) -- top pages object(s) in pages_obj_no
    pages_obj_no = []
    top_pages_obj_no = []
    for ind in inds:
        if (ind not in pages_obj_no) and (ind not in top_pages_obj_no):
            if find(pdf, bytes("\r{0} 0 obj".format(ind), "utf-8")) == -1:
                top_pages_obj_no.append(ind)
            else:
                pages_obj_no.append(ind)
    single_pages_obj_missed = len(top_pages_obj_no) == 1
    multi_pages_obj_missed = len(top_pages_obj_no) > 1
    # generate catalog object
    catalog_obj_no = fnd_unuse_no(obj_no, top_pages_obj_no)
    obj_no.append(catalog_obj_no)
    root_pages_obj_no = None
    if multi_pages_obj_missed:
        root_pages_obj_no = fnd_unuse_no(obj_no, top_pages_obj_no)
    elif single_pages_obj_missed:
        root_pages_obj_no = top_pages_obj_no[0]
        top_pages_obj_no = pages_obj_no
    else:  # root pages object exists, then find the root pages object #
        found = False
        for pon in pages_obj_no:
            tmp_addr = find(pdf, bytes("\r{0} 0 obj".format(pon), "utf-8"))
            while True:
                pdf.seek(tmp_addr)
                [_str] = struct.unpack("6s", pdf.read(6))
                if _str == b"Parent":
                    break
                elif _str == b"endobj":
                    root_pages_obj_no = pon
                    found = True
                    break
                tmp_addr = tmp_addr + 1
            if found:
                break
    catalog = bytes(
        "{0} 0 obj\r<</Type /Catalog\r/Pages {1} 0 R\r>>\rendobj\r".format(
            catalog_obj_no, root_pages_obj_no
        ),
        "utf-8",
    )
    pdf_data += catalog
    pdf.close()
    with open("pdf.tmp", "wb") as f:
        f.write(pdf_data)
    pdf = open("pdf.tmp", "rb")

    # Add Pages obj and EOF mark
    # if root pages object exist, pass
    # deal with single missing pages object
    if single_pages_obj_missed or multi_pages_obj_missed:
        inds_str = ["{0} 0 R".format(i) for i in top_pages_obj_no]
        kids_str = "[{0}]".format(" ".join(inds_str))
        pages_str = "{0} 0 obj\r<<\r/Type /Pages\r/Kids {1}\r/Count {2}\r>>\rendobj\r".format(
            root_pages_obj_no, kids_str, page_num
        )
        pdf_data += bytes(pages_str, "utf-8")
        pdf.close()
        with open("pdf.tmp", "wb") as f:
            f.write(pdf_data)
        pdf = open("pdf.tmp", "rb")
    # deal with multiple missing pages objects
    if multi_pages_obj_missed:
        kids_dict = {i: [] for i in top_pages_obj_no}
        count_dict = {i: 0 for i in top_pages_obj_no}
        for tpon in top_pages_obj_no:
            kids_addr = find_all(pdf, bytes("/Parent {0} 0 R".format(tpon), "utf-8"))
            for kid in kids_addr:
                ind = fnd_rvrs(pdf, b"obj", kid) - 4
                addr = fnd_rvrs(pdf, b"\r", ind)
                length = find(pdf, b" ", addr) - addr
                pdf.seek(addr)
                [ind] = struct.unpack(str(length) + "s", pdf.read(length))
                kids_dict[tpon].append(int(ind))
                type_addr = find(pdf, b"/Type", addr) + 5
                tmp_addr = find(pdf, b"/", type_addr) + 1
                pdf.seek(tmp_addr)
                [_type] = struct.unpack("5s", pdf.read(5))
                if _type == b"Pages":
                    cnt_addr = find(pdf, b"/Count ", addr) + 7
                    pdf.seek(cnt_addr)
                    [_str] = struct.unpack("1s", pdf.read(1))
                    cnt_len = 0
                    while _str not in [b" ", b"\r", b"/"]:
                        cnt_len += 1
                        pdf.seek(cnt_addr + cnt_len)
                        [_str] = struct.unpack("1s", pdf.read(1))
                    pdf.seek(cnt_addr)
                    [cnt] = struct.unpack(str(cnt_len) + "s", pdf.read(cnt_len))
                    count_dict[tpon] += int(cnt)
                else:  # _type == b"Page"
                    count_dict[tpon] += 1
            kids_no_str = ["{0} 0 R".format(i) for i in kids_dict[tpon]]
            kids_str = "[{0}]".format(" ".join(kids_no_str))
            pages_str = "{0} 0 obj\r<<\r/Type /Pages\r/Kids {1}\r/Count {2}\r>>\rendobj\r".format(
                tpon, kids_str, count_dict[tpon]
            )
            pdf_data += bytes(pages_str, "utf-8")
    pdf_data += bytes("\n%%EOF\r", "utf-8")
    pdf.close()
    with open("pdf.tmp", "wb") as f:
        f.write(pdf_data)

    # Use mutool to repair xref
    try:
        check_output(["pymupdf", "clean", "pdf.tmp", "pdf_toc.pdf"], stderr=STDOUT)
    except CalledProcessError as e:
        print(e.output.decode("utf-8"))
        raise SystemExit(
            "Command mutool returned non-zero exit status " + str(e.returncode)
        )
    os.remove("pdf.tmp")


def get_toc(fp: BinaryIO, toc_num_offset: int, toc_num: int):
    toc = []
    for i in range(toc_num):
        fp.seek(toc_num_offset + 4 + 0x134 * i)
        toc_bytes = struct.unpack("256s24s12s12si", fp.read(0x134))
        ttl_end = toc_bytes[0].find(b"\x00")
        title = toc_bytes[0][0:ttl_end].decode("gb18030").encode("utf-8")
        pg_end = toc_bytes[2].find(b"\x00")
        page = int(toc_bytes[2][0:pg_end])
        level = toc_bytes[4]
        toc_entry = {"title": title, "page": page, "level": level}
        toc.append(toc_entry)
    return toc


class Node(object):
    def __init__(self, data, parent=None, lchild=None, rchild=None):
        self.data = data
        self.parent = parent
        self.lchild = lchild
        self.rchild = rchild

    @property
    def level(self):
        return self.data["level"]

    @property
    def index(self):
        return self.data["index"]

    def real_parent(self):
        p = self
        while True:
            c = p
            p = p.parent
            if p.lchild == c:
                return p
            if p.parent is None:
                return None

    def prev(self):
        if self.parent.rchild == self:
            return self.parent
        else:
            return None

    def next(self):
        return self.rchild

    def first(self):
        return self.lchild

    def last(self):
        f = self.first()
        if f is None:
            return None
        r = f
        while r.rchild is not None:
            r = r.rchild
        return r


class BTree(object):
    def __init__(self):
        self.root = Node({"level": 0, "index": 0}, None)
        self.cursor = self.root

    @property
    def current_level(self):
        return self.cursor.level

    def insert_as_lchild(self, node):
        self.cursor.lchild = node
        node.parent = self.cursor
        self.cursor = node

    def insert_as_rchild(self, node):
        self.cursor.rchild = node
        node.parent = self.cursor
        self.cursor = node


def build_outlines_btree(toc):
    tree = BTree()
    for i, t in enumerate(toc):
        t["page"] -= 1  # Page starts at 0.
        t["index"] = i + 1
        node = Node(t)
        if t["level"] > tree.current_level:
            tree.insert_as_lchild(node)
        elif t["level"] == tree.current_level:
            tree.insert_as_rchild(node)
        else:
            while True:
                p = tree.cursor.real_parent()
                tree.cursor = p
                if p.level == t["level"]:
                    tree.insert_as_rchild(node)
                    break
        t["node"] = node


def make_dest(pdfw, pg):
    d = ArrayObject()
    try:
        d.append(pdfw.pages[pg].indirect_ref)
    except AttributeError:
        d.append(pdfw.pages[pg].indirect_reference)
    d.append(NameObject("/XYZ"))
    d.append(NullObject())
    d.append(NullObject())
    d.append(NullObject())
    return d


def fnd_unuse_no(nos1, nos2):
    unuse_no = -1
    for i in range(99999):
        if (99999 - i not in nos1) and (99999 - i not in nos2):
            unuse_no = 99999 - i
            break
    if unuse_no == -1:
        raise SystemExit("Error on PDF objects numbering.")
    return unuse_no


def find(fp: BinaryIO, s: bytes, start: int = 0):
    """查找文件中某个字节串的位置"""
    size = fp.seek(0, os.SEEK_END)  # 将指针移动到文件最后, 返回文件大小
    buff_size = 4096
    fp.seek(start)
    overlap = len(s) - 1
    while True:
        if overlap <= fp.tell() < size:  # tell()返回当前指针位置
            fp.seek(fp.tell() - overlap)
        buffer = fp.read(buff_size)
        if buffer:
            pos = buffer.find(s)
            if pos >= 0:
                return fp.tell() - (len(buffer) - pos)
        else:
            return -1


def find_all(data: bytes, search_bytes: bytes) -> list:
    """
    从data中找出所有的search_bytes开始位置
    :param data: 二进制数据
    :param search_bytes: 搜索的字节串
    :return: 所有的匹配的位置
    """
    pattern = re.compile(search_bytes)
    return [matched.start() for matched in pattern.finditer(data)]


def fnd_rvrs(f, s, end=sys.maxsize):
    # find target in reverse direction
    fsize = f.seek(0, os.SEEK_END)
    bsize = 4096
    if len(s) > end:
        raise SystemExit("Too large string size for search.")
    f.seek(fsize - bsize)
    buffer = None
    size = bsize
    if bsize <= end < fsize:
        f.seek(end - bsize)
    elif 0 < end < bsize:
        size = end
        f.seek(0)
    overlap = len(s) - 1
    s = s[::-1]
    while True:
        buffer = f.read(size)
        if buffer:
            buffer = buffer[::-1]
            pos = buffer.find(s)
            if pos >= 0:
                return f.tell() - pos
        if (2 * bsize - overlap) < f.tell():
            f.seek(f.tell() - (2 * bsize - overlap))
            size = bsize
        elif (bsize - overlap) < f.tell():
            size = f.tell() - (bsize - overlap)
            f.seek(0)
        else:
            return -1
