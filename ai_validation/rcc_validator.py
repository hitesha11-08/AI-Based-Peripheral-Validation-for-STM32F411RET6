RCC_AHB1ENR = 0x40023830

# GPIO clock-enable bit positions in AHB1ENR
GPIO_CLOCK_BITS = {
    "GPIOA": 0,
    "GPIOB": 1,
    "GPIOC": 2,
    "GPIOD": 3,
    "GPIOE": 4,
    "GPIOH": 7,
}

# MODER reset defaults per port (GPIOA's first two pins default to
# AF on the F411 Nucleo boards' SWD pins; everything else is 0 = input)
GPIO_MODER_BASE = {
    "GPIOA": 0x40020000,
    "GPIOB": 0x40020400,
    "GPIOC": 0x40020800,
    "GPIOD": 0x40020C00,
    "GPIOE": 0x40021000,
    "GPIOH": 0x40021C00,
}

GPIO_MODER_RESET_DEFAULT = {
    "GPIOA": 0xA8000000,   # PA13/PA14 default to SWD AF mode
    "GPIOB": 0x00000000,
    "GPIOC": 0x00000000,
    "GPIOD": 0x00000000,
    "GPIOE": 0x00000000,
    "GPIOH": 0x00000000,
}


def validate_rcc(reader):

    ahb1enr = reader.read32(RCC_AHB1ENR)

    report = {}

    for port, bit in GPIO_CLOCK_BITS.items():

        clock_enabled = (ahb1enr >> bit) & 1

        # -----------------------------------------
        # Clock never turned on -> port is simply
        # not used by this firmware. Not a fault.
        # -----------------------------------------
        if clock_enabled == 0:
            report[port] = "NOT_USED"
            continue

        # -----------------------------------------
        # Clock is on. Check whether the port was
        # actually configured (MODER changed from
        # reset default) or whether the clock was
        # enabled but the port left unused - this
        # second case is the real fault: wasted
        # clock / leftover init code.
        # -----------------------------------------
        moder_addr = GPIO_MODER_BASE[port]
        moder = reader.read32(moder_addr)
        reset_default = GPIO_MODER_RESET_DEFAULT[port]

        if moder == reset_default:
            # clock on, but pins never configured
            report[port] = "FAIL"
        else:
            report[port] = "PASS"

    return report