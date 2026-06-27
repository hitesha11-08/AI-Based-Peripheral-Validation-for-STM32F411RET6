I2C1_CR1 = 0x40005400
I2C1_CR2 = 0x40005404
I2C1_SR1 = 0x40005414
I2C1_SR2 = 0x40005418

def validate_i2c(reader):

    cr1 = reader.read32(I2C1_CR1)

    pe = cr1 & 0x1

    # -----------------------------------------
    # I2C never enabled -> NOT_USED, not a fault
    # -----------------------------------------
    if pe == 0:
        return {
            "Enabled" : "NOT_USED",
            "BusBusy" : "-",
            "BusError" : "-",
            "ArbitrationLost" : "-",
            "AckFailure" : "-"
        }

    sr1 = reader.read32(I2C1_SR1)
    sr2 = reader.read32(I2C1_SR2)

    busy = (sr2 >> 1) & 1

    berr = (sr1 >> 8) & 1
    arlo = (sr1 >> 9) & 1
    af   = (sr1 >> 10) & 1

    # -----------------------------------------
    # I2C is enabled - only real bus faults
    # should mark this FAIL
    # -----------------------------------------
    fault = bool(berr or arlo or af)
    status = "FAIL" if fault else "PASS"

    report = {
        "Enabled" : status,
        "BusBusy" : busy,
        "BusError" : berr,
        "ArbitrationLost" : arlo,
        "AckFailure" : af
    }

    return report