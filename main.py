# MAX7219 driver for micropython, changable font
# by Davood Hakemi @ElectroHakemi
#
# max7219.py is modified to work with user-define-able font
# used font github : https://github.com/easytarget/microPyEZfonts

from machine import SPI, SoftSPI, Pin
from micropython import const
from max7219 import Matrix8x8
import ezFBfont_5x7_ascii_07 as font

max_clk = const(18)
max_din = const(23)
max_cs = const(5)

# spi = SoftSPI(sck=max_clk, mosi=max_din, miso=19)
spi = SPI(2)

# display = Matrix8x8(spi, Pin(max_cs), 1, False)
display = Matrix8x8(spi, Pin(max_cs), 1, font, False)

display.brightness(10)

text = 'ElectroHakemi'

while True:
  display.scroll(text, 50, prefix='')
