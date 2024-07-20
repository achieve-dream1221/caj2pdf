#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/20 下午2:16
# @Author  : ACHIEVE_DREAM
# @File    : pymupdftest.py
# @Software: Pycharm
import pymupdf

if __name__ == "__main__":
    doc = pymupdf.open(r"F:\Wechat\WeChat Files\wxid_m7nzxhfolmcy22\FileStorage\File\2024-07\绘图2 1.pdf")  # open a document

    for page_index in range(len(doc)):  # iterate over pdf pages
        page = doc[page_index]  # get the page
        image_list = page.get_images()

        # print the number of images found on the page
        if image_list:
            print(f"Found {len(image_list)} images on page {page_index}")
        else:
            print("No images found on page", page_index)

        for image_index, img in enumerate(image_list, start=1):  # enumerate the image list
            xref = img[0]  # get the XREF of the image
            pix = pymupdf.Pixmap(doc, xref)  # create a Pixmap
            if pix.n - pix.alpha > 3:  # CMYK: convert to RGB first
                pix = pymupdf.Pixmap(pymupdf.CS_RGB, pix)

            pix.save("page_%s-image_%s.png" % (page_index, image_index))  # save the image as png
