SPI1_CR1 = 0x40013000
SPI1_CR2 = 0x40013004
SPI1_SR  = 0x40013008

def validate_spi(reader):

    cr1 = reader.read32(SPI1_CR1)

    spe = (cr1 >> 6) & 1

    # -----------------------------------------
    # SPI never enabled -> NOT_USED, not a fault
    # -----------------------------------------
    if spe == 0:
        return {
            "Enabled" : "NOT_USED",
            "MasterMode" : "-",
            "TXE" : "-",
            "RXNE" : "-",
            "Overrun" : "-",
            "Busy" : "-"
        }

    sr = reader.read32(SPI1_SR)

    mstr = (cr1 >> 2) & 1

    txe  = (sr >> 1) & 1
    rxne = (sr >> 0) & 1
    ovr  = (sr >> 6) & 1
    bsy  = (sr >> 7) & 1

    # -----------------------------------------
    # SPI is enabled - only a real fault
    # (overrun) should mark this FAIL
    # -----------------------------------------
    status = "FAIL" if ovr else "PASS"

    report = {
        "Enabled" : status,
        "MasterMode" : mstr,
        "TXE" : txe,
        "RXNE" : rxne,
        "Overrun" : ovr,
        "Busy" : bsy
    }

    return report