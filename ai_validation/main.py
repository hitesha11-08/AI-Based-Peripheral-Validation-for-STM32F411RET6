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


def print_section(title):

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


reader = STM32Reader()

try:

    print_section(
        "STM32F411RE AI VALIDATION REPORT"
    )

    # RCC

    print_section("RCC STATUS")

    rcc = validate_rcc(reader)

    for k, v in rcc.items():
        print(f"{k:20s}: {v}")

    # GPIO

    print_section("GPIO STATUS")

    gpio = validate_gpio(reader)

    for k, v in gpio.items():
        print(f"{k:20s}: {v}")

    # USART

    print_section("USART STATUS")

    usarts = validate_usarts(reader)

    for uart, data in usarts.items():

        print(f"\n{uart}")

        for field, val in data.items():
            print(f"  {field:15s}: {val}")

    # SPI

    print_section("SPI STATUS")

    spi = validate_spi(reader)

    for k, v in spi.items():
        print(f"{k:20s}: {v}")

    # I2C

    print_section("I2C STATUS")

    i2c = validate_i2c(reader)

    for k, v in i2c.items():
        print(f"{k:20s}: {v}")

    # ADC

    print_section("ADC STATUS")

    adc = validate_adc(reader)

    for k, v in adc.items():
        print(f"{k:20s}: {v}")

    # PWM

    print_section("PWM STATUS")

    pwm = validate_pwm(reader)

    for k, v in pwm.items():
        print(f"{k:20s}: {v}")

    # TIMERS

    print_section("TIMER STATUS")

    timers = validate_timers(reader)

    for k, v in timers.items():
        print(f"{k:20s}: {v}")

    # DMA
    # NOTE: DMA is core silicon on this part and is always actively
    # evaluated -> never reported as NOT_USED, per validator design.

    print_section("DMA STATUS")

    dma = validate_dma(reader)

    for k, v in dma.items():
        print(f"{k:20s}: {v}")

    # SysTick

    print_section("SYSTICK STATUS")

    systick = validate_systick(reader)

    for k, v in systick.items():
        print(f"{k:20s}: {v}")

    # NVIC
    # NOTE: NVIC is core silicon and is always actively evaluated ->
    # never reported as NOT_USED, per validator design.

    print_section("NVIC STATUS")

    nvic = validate_nvic(reader)

    for k, v in nvic.items():
        print(f"{k:20s}: {v}")

finally:

    reader.close()

    print("\nValidation Complete")