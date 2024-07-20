#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/18 下午8:08
# @Author  : ACHIEVE_DREAM
# @File    : main.py
# @Software: Pycharm
# import typer
from caj2pdf import convert

# def main(src: str, dest: str = None):
#     convert(src, dest)


if __name__ == "__main__":
    # typer.run(main)
    convert("../target/caj/caj.caj")
