# main.py – put your code here!
# -*- coding:utf-8 -*-
# @Author : Dedicatus1979
# @GitHub : github.com/Dedicatus1979

"""
该文件为系统的主程序，单片机开机运行该程序
"""

import uos
from machine import I2C, Pin, Timer
from utime import sleep_ms
from ustruct import pack
from max30102 import MAX30102, MAX30105_PULSE_AMP_HIGH
from some_other import HRMonitor, Screen, MAX30205

SAMPLE_TIME = 30
SAMPLE_RATE = 400
SAMPLE_AVE = 8
SAMPLE_FREQUENCY = 50
CYCLE = 0.02
LED_MODE = 1
LED_POWER = MAX30105_PULSE_AMP_HIGH

SOLIDUS_TIME = 0.65

RED_FILE = 'red.bin'

I2C1_SCL = Pin('PB6')
I2C1_SDA = Pin('PB7')
I2C2_SCL = Pin('PB10')
I2C2_SDA = Pin('PB3')
RESET = Pin('PB0', Pin.OUT)

RESET.value(1)
ResetState = 1
Main = 0
DownSide = 0
LowTimes = 0

i2c_1 = I2C(sda=I2C1_SDA, scl=I2C1_SCL, freq=400000)
HR_sensor = MAX30102(i2c=i2c_1)
temp_sensor = MAX30205(i2c_1)

i2c_2 = I2C(sda=I2C2_SDA, scl=I2C2_SCL, freq=400000)
ssd1306 = Screen(i2c_2)

def ResetMonitor(t):
    global ResetState, DownSide, LowTimes
    if RESET.value() != ResetState and RESET.value() == 0:
        sleep_ms(10)
        if RESET.value() == 0:
            ResetState = 0

    if RESET.value() != ResetState and RESET.value() == 1:
        sleep_ms(10)
        if RESET.value() == 1:
            ResetState = 1
            if LowTimes < 40:
                DownSide = 1
            LowTimes = 0

    if ResetState == 0:
        LowTimes += 1
        if LowTimes >= 40:
            ssd1306.clear()
            ssd1306.show()
            try:
                HR_sensor.shutdown()
            except:
                pass
            DownSide = 0
    else:
        LowTimes = 0

def main():
    global Main
    print("程序开始运行")
    ssd1306.clear()
    uos.remove(RED_FILE)
    t2 = open(RED_FILE, 'ab')
    H_M = HRMonitor(SAMPLE_FREQUENCY)
    TSample = 0
    Index = 0
    Blocks = 0

    i2c_1.scan()
    HR_sensor.setup_sensor(led_mode=LED_MODE, sample_rate=SAMPLE_RATE,
                           led_power=LED_POWER, sample_avg=SAMPLE_AVE,
                           pulse_width=411)
    if DownSide == 1:
        Main = 0
        return None

    ssd1306.progress("请稍候...", [30, 0, 16], [0, 32, 16])
    ssd1306.show()

    while True:
        HR_sensor.check()
        if HR_sensor.available():
            red_reading = HR_sensor.pop_red_from_storage()
            if red_reading < 10000:
                ssd1306.clear()
                ssd1306.write("无手指", 38, 25, 16)
                ssd1306.show()
                while True:
                    sleep_ms(100)
                    if ResetState == 0:
                        if LowTimes >= 40:
                            break
            t2.write(pack(">H", red_reading))
            TSample += 1
            H_M.linear_fast_HR_lower(red_reading, TSample)
        if TSample >= SAMPLE_FREQUENCY * SAMPLE_TIME:
            ssd1306.upgrade_progress_half(Blocks, Index, True)
            ssd1306.show()
            break
        if ((TSample * CYCLE) // SOLIDUS_TIME) % 2 != Index:
            if (TSample * 14) // (SAMPLE_FREQUENCY * SAMPLE_TIME) > Blocks:
                Blocks += 1
            Index = (Index + 1) % 2
            ssd1306.upgrade_progress_half(Blocks, Index)
            ssd1306.show()
        if DownSide == 1:
            Main = 0
            return None
    HR_sensor.shutdown()

    if DownSide == 1:
        Main = 0
        return None

    ssd1306.progress("数据处理中...", [12, 0, 16], [0, 32, 16])
    ssd1306.show()
    tem = temp_sensor.read_temperature()
    t2.write(pack(">H", int(tem * 100)))
    t2.close()
    Blocks = 0
    while True:
        ssd1306.upgrade_progress_full(Blocks)
        ssd1306.show()
        Blocks += 1
        sleep_ms(int(SOLIDUS_TIME * 320))
        if Blocks == 7:
            ssd1306.upgrade_progress_full(Blocks, True)
            ssd1306.show()
            break

        if DownSide == 1:
            Main = 0
            return None

    ssd1306.clear()
    HR = round(60 / H_M.denoise_cycle())
    ssd1306.show_health_info(HR, tem)
    ssd1306.show()
    Main = 0


if __name__ == '__main__':
    tim = Timer()
    tim.init(period=33, mode=Timer.PERIODIC, callback=ResetMonitor)
    ssd1306.write("按下按键后", 24, 12, 16)
    ssd1306.write("进行测量", 30, 38, 16)
    ssd1306.show()
    while True:
        if Main == 1:
            main()
        if DownSide == 0:
            continue
        if Main == 0:
            Main = 1
            DownSide = 0
