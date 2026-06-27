from register_reader import STM32Reader

from rcc_validator import validate_rcc
from gpio_validator import validate_gpio
from usart_validator import validate_usarts
from spi_validator import validate_spi
from i2c_validator import validate_i2c
from adc_validator import validate_adc
from pwm_validator import validate_pwm
from timer_validator import validate_timers
from dma_validator import validate_dma
from systick_validator import validate_systick
from nvic_validator import validate_nvic


def get_status():

    reader = STM32Reader()

    try:

        rcc = validate_rcc(reader)
        gpio = validate_gpio(reader)
        usarts = validate_usarts(reader)
        spi = validate_spi(reader)
        i2c = validate_i2c(reader)
        adc = validate_adc(reader)
        pwm = validate_pwm(reader)
        timers = validate_timers(reader)
        dma = validate_dma(reader)
        systick = validate_systick(reader)
        nvic = validate_nvic(reader)

        status = {

            "uart_status":
            1 if usarts["USART2"]["Enabled"] else 0,

            "i2c_status":
            1 if i2c["Enabled"] == "PASS" else 0,

            "spi_status":
            1 if spi["Enabled"] == "PASS" else 0,

            "adc_status":
            1 if adc["ADC Enabled"] == "PASS" else 0,

            "pwm_status":
            1 if pwm["Timer Running"] == "PASS" else 0,

            "timer_status":
            1,

            "nvic_status":
            1 if nvic["USART2_IRQ"] else 0,

            "dma_status":
            1 if dma["DMA_ERROR"] == 0 else 0,

            "gpio_status":
            1,

            "rcc_status":
            1 if rcc["GPIOA"] == "PASS" else 0
        }

        return status

    finally:

        reader.close()