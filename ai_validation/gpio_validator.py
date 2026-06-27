GPIOA_MODER = 0x40020000
GPIOB_MODER = 0x40020400

def validate_gpio(reader):

    gpioa = reader.read32(GPIOA_MODER)
    gpiob = reader.read32(GPIOB_MODER)

    return {
        "GPIOA_MODER": hex(gpioa),
        "GPIOB_MODER": hex(gpiob)
    }