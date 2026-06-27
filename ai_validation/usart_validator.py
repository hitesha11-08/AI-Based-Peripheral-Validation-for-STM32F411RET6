USART1_SR  = 0x40011000
USART1_CR1 = 0x4001100C

USART2_SR  = 0x40004400
USART2_CR1 = 0x4000440C

USART6_SR  = 0x40011400
USART6_CR1 = 0x4001140C


def check_uart(reader, sr_addr, cr1_addr):
    cr1 = reader.read32(cr1_addr)
    sr  = reader.read32(sr_addr)

    ue = (cr1 >> 13) & 1
    te = (cr1 >> 3) & 1
    re = (cr1 >> 2) & 1

    txe  = (sr >> 7) & 1
    rxne = (sr >> 5) & 1
    ore  = (sr >> 3) & 1
    ne   = (sr >> 2) & 1
    fe   = (sr >> 1) & 1
    pe   = (sr >> 0) & 1

    if ue == 0:
        return {
            "Enabled": "NOT USED",
            "Status": "NOT USED",
            "TX": "-",
            "RX": "-",
            "Overrun": 0,
            "ParityError": 0,
            "FramingError": 0,
            "NoiseError": 0
        }

    fault = ore or pe or fe or ne

    return {
        "Enabled": "PASS",
        "Status": "FAIL" if fault else "PASS",
        "TX": "PASS" if te and txe else "FAIL" if te else "NOT USED",
        "RX": "PASS" if re and rxne else "FAIL" if re else "NOT USED",
        "Overrun": 1 if ore else 0,
        "ParityError": 1 if pe else 0,
        "FramingError": 1 if fe else 0,
        "NoiseError": 1 if ne else 0
    }


def validate_usarts(reader):
    return {
        "USART1": check_uart(reader, USART1_SR, USART1_CR1),
        "USART2": check_uart(reader, USART2_SR, USART2_CR1),
        "USART6": check_uart(reader, USART6_SR, USART6_CR1)
    }