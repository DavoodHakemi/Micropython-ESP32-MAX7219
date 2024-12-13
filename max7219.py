# MicroPython max7219 8x8 LED matrix driver, cascadable, SPI interface

from micropython import const
import framebuf
from utime import sleep_ms
import uasyncio as asyncio

from writer import Writer
from writer import DisplayState

_NOOP = const(0)
_DIGIT0 = const(1)
_DECODEMODE = const(9)
_INTENSITY = const(10)
_SCANLIMIT = const(11)
_SHUTDOWN = const(12)
_DISPLAYTEST = const(15)

class NationalDisplay(framebuf.FrameBuffer):
    def __init__(self, width, height, buffer, mode):
        self.width = width
        self.height = height
        self.buffer = buffer
        self.mode = mode
        super().__init__(self.buffer, self.width, self.height, self.mode)

    def show(self):
        ...

class Matrix8x8:
    def __init__(self, spi, cs, num, font=None, vertical_mirror=True):
        """
        Driver for cascading MAX7219 8x8 LED matrices.

        >>> import max7219
        >>> from machine import Pin, SPI
        >>> spi = SPI(1)
        >>> display = max7219.Matrix8x8(spi, Pin('X5'), 4)
        >>> display.text('1234',0,0,1)
        >>> display.show()

        """
        self.spi = spi
        self.cs = cs
        self.cs.init(cs.OUT, True)
        self.buffer = bytearray(8 * num)
        self.num = num
        direction = framebuf.MONO_HMSB if vertical_mirror else framebuf.MONO_HLSB
        fb = framebuf.FrameBuffer(self.buffer, 8 * num, 8, direction)
        self.framebuf = fb
        # Provide methods for accessing FrameBuffer graphics primitives. This is a workround
        # because inheritance from a native class is currently unsupported.
        # http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
        self.fill = fb.fill  # (col)
        self.pixel = fb.pixel # (x, y[, c])
        self.hline = fb.hline  # (x, y, w, col)
        self.vline = fb.vline  # (x, y, h, col)
        self.line = fb.line  # (x1, y1, x2, y2, col)
        self.rect = fb.rect  # (x, y, w, h, col)
        self.fill_rect = fb.fill_rect  # (x, y, w, h, col)
        self.blit = fb.blit  # (fbuf, x, y[, key])

        self.font = font
        if self.font is not None:
            self.display = NationalDisplay(8 * num, 8, self.buffer, direction)
            self.writer = Writer(self.display, font)
            # Clip when screen fullt
            # Clip when row is full
            # Ignore skip blank spaces 
            self.writer.set_clip(True, True, False)

        self.init()

    def _write(self, command, data):
        self.cs(0)
        for m in range(self.num):
            self.spi.write(bytearray([command, data]))
        self.cs(1)

    def init(self):
        for command, data in (
            (_SHUTDOWN, 0),
            (_DISPLAYTEST, 0),
            (_SCANLIMIT, 7),
            (_DECODEMODE, 0),
            (_SHUTDOWN, 1),
        ):
            self._write(command, data)

    def text(self, message, xpos=0, ypos=0, color=1):
        self.fill(0)

        if self.font is None:
            self.framebuf.text(message, xpos, ypos, color)
        else:
            # modified self.writer.set_textpos(self.display, ypos, xpos)
            if xpos <= 0: xpos = xpos + self.display.width

            devid = id(self.display)
            if devid not in self.writer.state:
                self.writer.state[devid] = DisplayState()
            s = self.writer.state[devid]  # Current state

            s.text_col=xpos
            s.text_row=ypos
            # modified self.writer.set_textpos

            self.writer.printstring(message)

        self.show()

    def brightness(self, value):
        if not 0 <= value <= 15:
            raise ValueError("Brightness out of range")
        self._write(_INTENSITY, value)

    def show(self):
        for y in range(8):
            self.cs(0)
            for m in range(self.num):
                self.spi.write(bytearray([_DIGIT0 + y, self.buffer[(y * self.num) + m]]))
            self.cs(1)

    # The following two functions should be carved out into another file so
    # users don't have to pay for the imports unless they want the
    # functionality.

    def scroll(self, text, delay=10, distance=None, prefix='  '):
        ''' Scrolls text distance pixels to the left with delay ms between
        rendering each frame. Prefix is intended to give the user a chance
        to see the text before it is slid off. '''
        text = prefix + text
        if not distance:
            distance = len(text) * 8
        for i in range(distance):
            self.text(text, -i)
            sleep_ms(delay)

    async def async_scroll(self, text, delay=10, distance=None, prefix='  '):
        ''' Scrolls text distance pixels to the left with delay ms between
        rendering each frame. Prefix is intended to give the user a chance
        to see the text before it is slid off. '''
        text = prefix + text
        if not distance:
            distance = len(text) * 8
        for i in range(distance):
            self.text(text, -i)
            await asyncio.sleep_ms(delay)
