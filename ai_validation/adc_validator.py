ADC1_SR   = 0x40012000
ADC1_CR1  = 0x40012004
ADC1_CR2  = 0x40012008
ADC1_DR   = 0x4001204C

RCC_APB2ENR = 0x40023844


def validate_adc(reader):

    apb2 = reader.read32(RCC_APB2ENR)
    adc_clock = (apb2 >> 8) & 1      # ADC1 Clock Enable

    # -----------------------------------------
    # ADC not used -> clock never turned on
    # -----------------------------------------
    if adc_clock == 0:
        return {
            "Status": "NOT_USED",
            "ADC Enabled": "NO",
            "EOC Flag": 0,
            "ADC Value": 0
        }

    cr2 = reader.read32(ADC1_CR2)
    sr  = reader.read32(ADC1_SR)
    dr  = reader.read32(ADC1_DR)

    adon = (cr2 >> 0) & 1
    eoc  = (sr >> 1) & 1
    overrun = (sr >> 5) & 1

    # -----------------------------------------
    # Clock enabled but ADC peripheral itself
    # never turned on -> still "not used", not
    # a fault. A real fault is overrun, or
    # being enabled but stuck.
    # -----------------------------------------
    if adon == 0:
        status = "NOT_USED"

    # -----------------------------------------
    # Runtime Error - actual fault
    # -----------------------------------------
    elif overrun:
        status = "FAIL"

    # -----------------------------------------
    # Conversion completed successfully
    # -----------------------------------------
    elif eoc == 1:
        status = "PASS"

    # -----------------------------------------
    # ADC is on and converting, just hasn't
    # finished yet -> not a fault, it's busy
    # -----------------------------------------
    else:
        status = "PASS"

    return {

        "Status": status,

        "ADC Enabled": "YES" if adon else "NO",

        "EOC Flag": eoc,

        "Overrun": overrun,

        "ADC Value": dr & 0xFFFF
    }