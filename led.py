#!/usr/bin/env python3
import mmap
import os
import struct
import time

# 常量定义（与汇编/C代码保持一致） 
GPIO_BASE   = 0xFE200000   # GPIO 控制器物理基地址 (Raspberry Pi 4)
MAP_LEN     = 4096         # 映射长度 4KB

GPFSEL4_OFF = 0x10         # GPIO Function Select 4 (GPIO40–49)
GPSET1_OFF  = 0x20         # GPIO Pin Output Set 1 (GPIO32–53)
GPCLR1_OFF  = 0x2C         # GPIO Pin Output Clear 1 (GPIO32–53)

LED_GPIO = 42
LED_BIT  = LED_GPIO - 32   # 在 GPSET1/GPCLR1 中的 bit 位置


def main():
    # 打开 /dev/mem
    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)

    # 映射 GPIO 控制寄存器
    mem = mmap.mmap(fd, MAP_LEN, mmap.MAP_SHARED,
                    mmap.PROT_READ | mmap.PROT_WRITE,
                    offset=GPIO_BASE)

    def read_reg(offset):
        mem.seek(offset)
        data = mem.read(4)
        return struct.unpack("<I", data)[0]

    def write_reg(offset, value):
        mem.seek(offset)
        mem.write(struct.pack("<I", value))

    # 1. 配置 GPIO42 为输出 
    val = read_reg(GPFSEL4_OFF)
    val &= ~(0x7 << 6)   # 清除 GPIO42 的功能位
    val |=  (0x1 << 6)   # 设置为输出 (001)
    write_reg(GPFSEL4_OFF, val)

    # 2. 点亮 LED (写 GPSET1) 
    write_reg(GPSET1_OFF, (1 << LED_BIT))

    # 3. 等待 3 秒 
    time.sleep(3)

    # 4. 熄灭 LED (写 GPCLR1) 
    write_reg(GPCLR1_OFF, (1 << LED_BIT))

    # 5. 清理
    mem.close()
    os.close(fd)

    print("LED test done")


if __name__ == "__main__":
    main()
