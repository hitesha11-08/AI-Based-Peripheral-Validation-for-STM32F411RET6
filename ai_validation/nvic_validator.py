NVIC_ISER0 = 0xE000E100   # Interrupt Set-Enable Register
NVIC_ISPR0 = 0xE000E200   # Interrupt Set-Pending Register
NVIC_IABR0 = 0xE000E300   # Interrupt Active Bit Register

# STM32F411 vector table IRQ numbers for the peripherals we care about
IRQ_NUMBERS = {
    "ADC_IRQ":    18,
    "TIM2_IRQ":   28,
    "I2C1_IRQ":   31,   # I2C1_EV
    "SPI1_IRQ":   35,
    "USART2_IRQ": 38,
}


def _read_bit(reader, base_addr, irq_num):
    reg_addr = base_addr + (4 * (irq_num // 32))
    bit = irq_num % 32
    val = reader.read32(reg_addr)
    return (val >> bit) & 1


def _check_irq(reader, irq_num):

    enabled = _read_bit(reader, NVIC_ISER0, irq_num)
    pending = _read_bit(reader, NVIC_ISPR0, irq_num)
    active  = _read_bit(reader, NVIC_IABR0, irq_num)

    # -----------------------------------------
    # NVIC is core to the MCU, always actively
    # evaluated. A real fault here is an
    # interrupt that is pending but masked
    # (disabled) - meaning an event fired and
    # is being missed/never serviced.
    # -----------------------------------------
    fault = bool(pending and not enabled)

    status = "FAIL" if fault else "PASS"

    return {
        "Status": status,
        "Enabled": enabled,
        "Pending": pending,
        "Active": active
    }


def validate_nvic(reader):

    report = {}
    any_fault = False

    for name, irq_num in IRQ_NUMBERS.items():
        result = _check_irq(reader, irq_num)
        report[name] = result
        if result["Status"] == "FAIL":
            any_fault = True

    report["Status"] = "FAIL" if any_fault else "PASS"

    return report