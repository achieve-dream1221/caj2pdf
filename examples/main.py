#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/18 下午8:08
# @Author  : ACHIEVE_DREAM
# @File    : main.py
# @Software: Pycharm
# import typer
from caj2pdf import convert
from old.cajparser import CAJParser
from pathlib import Path

# def main(src: str, dest: str = None):
#     convert(src, dest)


if __name__ == "__main__":
    # typer.run(main)
    # for e in Path("../target/caj").glob("*.caj"):
    #     convert(str(e))
    convert(r"E:\pycharm\caj2pdf\target\caj\caj2.caj")
    # p = CAJParser(r"E:\pycharm\caj2pdf\target\caj\caj2.caj")
    # p.convert(r"E:\pycharm\caj2pdf\target\caj\caj2.pdf")
