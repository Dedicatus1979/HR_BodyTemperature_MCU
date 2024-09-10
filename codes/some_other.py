# -*- coding:utf-8 -*-
# @Time : 2024-02-22 下午 3:44
# @Author : Dedicatus1979

import ssd1306py as lcd

class FixedList:
    def __init__(self, maxlen):
        self._fl = []
        self._maxlen = maxlen

    def append(self, data):
        self._fl.append(data)
        if len(self._fl) > self._maxlen:
            self._fl.pop(0)

    def __getitem__(self, item):
        return self._fl[item]

    def __len__(self):
        return len(self._fl)

    def __max__(self):
        return max(self._fl)

    def __min__(self):
        return min(self._fl)


class HRMonitor:
    def __init__(self, frequency):
        self.frequency = frequency
        self.cycle = 1 / frequency
        self.row_list = FixedList(maxlen=3)
        self.locate_lower = 0
        self.locate_min = -125
        self.last_dif = 0
        self.minimum = 0
        self.locate_list = []

    def diff1(self):
        if len(self.row_list) < 3:
            return 0
        return int((self.row_list[2] - self.row_list[0]) / (2 * self.cycle))

    def linear_fast_HR_lower(self, data_row, index):
        self.row_list.append(data_row)
        dif = self.diff1()

        if self.last_dif >= 0 and dif >= 0:
            self.last_dif = dif
            return None
        if dif <= self.last_dif:
            self.locate_lower = index
        else:
            if index == self.locate_lower + 1:
                if (self.locate_lower - self.locate_min) * self.cycle > 0.25:
                    if self.minimum != 0:
                        if self.last_dif > self.minimum:
                            if abs((self.minimum - self.last_dif) / self.minimum) >= 0.68:
                                return None
                    self.locate_min = self.locate_lower
                    self.minimum = self.last_dif
                    self.locate_list.append(self.locate_min)
        self.last_dif = dif
        return None

    def denoise_cycle(self):
        interval = []
        last_pop = 0
        i = 1
        while True:
            if i >= len(self.locate_list):
                break
            t = self.locate_list[i] - self.locate_list[i - 1]
            if not interval:
                interval.append(t)
            else:
                last = interval[-1]
                if last * 0.82 <= t <= last * 1.18:
                    interval.append(t)
                else:
                    if t >= last * 2:
                        interval.append(self.locate_list[i] - last_pop)
                        i += 1
                        continue
                    last_pop = self.locate_list.pop(i)
                    continue
            i += 1
        try:
            return (sum(interval[5:]) / len(interval[5:])) * self.cycle
        except:
            return (sum(interval) / len(interval)) * self.cycle


class Screen:
    def __init__(self, i2c):
        self._progress_times = None
        self.lcd = lcd
        self.lcd.init_i2c(i2c, 128, 64)
        self._progress_locate = None

    def write(self, text, x_axis, y_axis, font_size):
        self.lcd.text(text, x_axis, y_axis, font_size)

    def show(self):
        self.lcd.show()

    def progress(self, progress_info, text_coord, progress_coord):
        self.write(progress_info, text_coord[0], text_coord[1], text_coord[2])
        self.write('[' + ' ' * 14 + ']', progress_coord[0], progress_coord[1], progress_coord[2])
        self._progress_times = 0
        self._progress_locate = progress_coord[1]

    def upgrade_progress_half(self, block, ind, last=False):
        if block < 14:
            if block:
                self.write('\uf8ff', block * 8, self._progress_locate, 16)
#             self.write(['/', '\\'][ind], (block + 1) * 8, self._progress_locate, 16)
        else:
            self.write('\uf8fd', block * 8, self._progress_locate, 16)
        if last:
            self.write('\uf8fd', 112, self._progress_locate, 16)

    def upgrade_progress_full(self, block, last=False):
        if block < 7:
            if block:
                self.write('\uf8fe', block * 16 - 8, self._progress_locate, 16)
        if last:
            self.write('\uf8fe', 104, self._progress_locate, 16)

    def show_health_info(self, HR, Temperature):
        HR_text = "心率:{:^6d}BPM".format(HR)
        Temperature_text = "体温:{:^6.1f}℃ ".format(Temperature)
        self.write(HR_text,8, 8, 16)
        self.write(Temperature_text, 8, 28, 16)
        self.write("(体表30s温度)", 16, 48, 16)

    def clear(self):
        self.lcd.clear()


class MAX30205:
    def __init__(self, i2c,):
        self._i2c = i2c
        self._address = 72
        self._temp_reg = 0

    def read_temperature(self):
        """读取体温传感器种的值"""
        data_raw = self._i2c.readfrom_mem(self._address, self._temp_reg, 2)
        raw = data_raw[0] << 8 | data_raw[1]
        # 将寄存器中的数据以整型数的形式读出，高8位（7位）为整数部分，第8位为小数部分，对二进制值移位后取或，即对高低值合并
        # 2^-8=0.00390625 即分辨率为0.00390625，将读到的值乘以分辨率即为体温值
        return raw * 0.00390625

