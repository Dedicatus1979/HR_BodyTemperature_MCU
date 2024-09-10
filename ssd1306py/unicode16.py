# -*- coding:utf-8 -*-
# @Time : 2024-03-06 下午 11:27
# @Author : Dedicatus1979
import ssd1306py.fonts16

_fonts = ssd1306py.fonts16.fonts


def display(oled, string, x_axis, y_axis):
    offset = 0
    for k in string:
        if ord(k) <= 127:
            notasc = 0
        else:
            notasc = 1
        code = k.encode()
        byte_data = _fonts[code]
        for y in range(0, 16):
            a = bin(byte_data[y]).replace('0b', '')
            while len(a) < 8:
                a = '0' + a
            if notasc:
                b = bin(byte_data[y + 16]).replace('0b', '')
                while len(b) < 8:
                    b = '0' + b
            for x in range(0, 8):
                oled.pixel(x_axis + offset + x, y + y_axis, int(a[x]))
                if notasc:
                    oled.pixel(x_axis + offset + x + 8, y + y_axis, int(b[x]))
        offset += (8 + notasc * 8)
