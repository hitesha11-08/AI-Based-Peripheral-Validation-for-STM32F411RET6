TIM3_CR1  = 0x40000400
TIM3_CNT  = 0x40000424
TIM3_PSC  = 0x40000428
TIM3_ARR  = 0x4000042C
TIM3_CCR1 = 0x40000434

def validate_pwm(reader):

    cr1 = reader.read32(TIM3_CR1)
    cen = cr1 & 1

    # -----------------------------------------
    # Timer never started -> NOT_USED, not a
    # fault. A timer that was never enabled
    # for PWM is simply unused.
    # -----------------------------------------
    if cen == 0:
        return {
            "Timer Running" : "NOT_USED",
            "Counter"       : "-",
            "Prescaler"     : "-",
            "ARR"           : "-",
            "CCR1"          : "-",
            "DutyCycle"     : "-"
        }

    cnt  = reader.read32(TIM3_CNT)
    psc  = reader.read32(TIM3_PSC)
    arr  = reader.read32(TIM3_ARR)
    ccr1 = reader.read32(TIM3_CCR1)

    if arr != 0:
        duty = (ccr1 * 100.0) / arr
    else:
        duty = 0

    # -----------------------------------------
    # Timer is running. A real fault here is
    # ARR == 0 while running (no period set,
    # PWM output is meaningless)
    # -----------------------------------------
    status = "FAIL" if arr == 0 else "PASS"

    report = {
        "Timer Running" : status,
        "Counter"       : cnt,
        "Prescaler"     : psc,
        "ARR"           : arr,
        "CCR1"          : ccr1,
        "DutyCycle"     : round(duty, 2)
    }

    return report