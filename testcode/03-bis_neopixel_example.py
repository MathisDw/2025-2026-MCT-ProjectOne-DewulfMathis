import board
import neopixel_spi

pixels = neopixel_spi.NeoPixel_SPI(board.SPI(), 72)
pixels.fill(0xff0000)
