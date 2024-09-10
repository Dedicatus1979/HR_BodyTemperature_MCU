"""
Copyright 2021-2021 The jdh99 Authors. All rights reserved.
ssd1306操作封装.支持多种英文字库
Authors: jdh99 <jdh821@163.com>
Make corrections and deletions with Dedicatus1979 at 2024-03-06
"""

import ssd1306py.ssd1306 as ssd1306
import ssd1306py.unicode16 as unicode16

_oled = None
_i2c = None
_width = 0
_height = 0


def init_i2c(i2c, width, height):
    global _oled, _width, _height
    _i2c = i2c
    _width = width
    _height = height
    _oled = ssd1306.SSD1306_I2C(_width, _height, _i2c)


def clear():
    global _oled
    _oled.fill(0)


def show():
    global _oled
    _oled.show()


def pixel(x, y):
    global _oled
    _oled.pixel(x, y, 1)


def text(string, x_axis, y_axis, font_size):
    global _oled
    if font_size != 8 and font_size != 16 and font_size != 24 and font_size != 32:
        return
    if font_size == 8:
        _oled.text(string, x_axis, y_axis)
        return
    if font_size == 16:
        unicode16.display(_oled, string, x_axis, y_axis)

