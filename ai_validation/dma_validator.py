DMA1_BASE = 0x40026000
DMA2_BASE = 0x40026400

LISR_OFFSET = 0x00
HISR_OFFSET = 0x04
SxCR_OFFSET_BASE = 0x10
SxCR_STRIDE = 0x18

# Bit offsets within LISR/HISR for streams 0-3 (same layout reused for 4-7)
# Each stream block: FEIF, DMEIF, TEIF, HTIF, TCIF
STREAM_BIT_BASE = {0: 0, 1: 6, 2: 16, 3: 22}


def _stream_error_flags(isr_value, stream_in_register):
    base = STREAM_BIT_BASE[stream_in_register]
    feif  = (isr_value >> (base + 0)) & 1
    dmeif = (isr_value >> (base + 2)) & 1
    teif  = (isr_value >> (base + 3)) & 1
    return feif, dmeif, teif


def _check_controller(reader, dma_base, name):

    lisr = reader.read32(dma_base + LISR_OFFSET)
    hisr = reader.read32(dma_base + HISR_OFFSET)

    enabled_streams = []
    fault_streams = []

    for stream in range(8):
        cr_addr = dma_base + SxCR_OFFSET_BASE + (stream * SxCR_STRIDE)
        cr = reader.read32(cr_addr)
        en = cr & 1

        if en:
            enabled_streams.append(stream)

        # streams 0-3 live in LISR, streams 4-7 live in HISR
        if stream < 4:
            feif, dmeif, teif = _stream_error_flags(lisr, stream)
        else:
            feif, dmeif, teif = _stream_error_flags(hisr, stream - 4)

        if feif or dmeif or teif:
            fault_streams.append(stream)

    status = "FAIL" if fault_streams else "PASS"

    return {
        f"{name}_Status": status,
        f"{name}_EnabledStreams": enabled_streams,
        f"{name}_FaultStreams": fault_streams
    }


def validate_dma(reader):

    # -----------------------------------------
    # DMA is core silicon, always clocked on
    # this part -> always actively evaluated,
    # never reported as NOT_USED.
    # -----------------------------------------
    report = {}

    report.update(_check_controller(reader, DMA1_BASE, "DMA1"))
    report.update(_check_controller(reader, DMA2_BASE, "DMA2"))

    overall_fail = (
        report["DMA1_Status"] == "FAIL" or
        report["DMA2_Status"] == "FAIL"
    )

    report["Status"] = "FAIL" if overall_fail else "PASS"

    return report