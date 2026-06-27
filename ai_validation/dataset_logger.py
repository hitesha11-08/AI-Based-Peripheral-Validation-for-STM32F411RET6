import csv
import time

from register_reader import STM32Reader

from rcc_validator import validate_rcc
from gpio_validator import validate_gpio
from usart_validator import validate_usarts
from i2c_validator import validate_i2c
from spi_validator import validate_spi
from adc_validator import validate_adc
from pwm_validator import validate_pwm

reader = STM32Reader()

csv_file = "stm32_validation_dataset.csv"

with open(csv_file, "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow([
        "Time",

        "USART2_EN",
        "USART2_TX",
        "USART2_RX",

        "I2C_EN",
        "I2C_BUSY",
        "I2C_ACK_FAIL",

        "SPI_EN",
        "SPI_TXE",
        "SPI_RXNE",

        "ADC_VALUE",

        "PWM_DUTY"
    ])

    try:

        while True:

            usart = validate_usarts(reader)

            i2c = validate_i2c(reader)

            spi = validate_spi(reader)

            adc = validate_adc(reader)

            pwm = validate_pwm(reader)

            row = [

                time.time(),

                usart["USART2"]["Enabled"],
                usart["USART2"]["TX"],
                usart["USART2"]["RX"],

                1 if i2c["Enabled"] == "PASS" else 0,
                i2c["BusBusy"],
                i2c["AckFailure"],

                1 if spi["Enabled"] == "PASS" else 0,
                spi["TXE"],
                spi["RXNE"],

                adc["ADC Value"],

                pwm["DutyCycle"]
            ]

            writer.writerow(row)

            f.flush()

            print(row)

            time.sleep(1)

    except KeyboardInterrupt:

        print("Dataset collection stopped")

        reader.close()