import joblib
import pandas as pd
import webbrowser
from datetime import datetime

from register_reader import STM32Reader

from rcc_validator import validate_rcc
from gpio_validator import validate_gpio
from usart_validator import validate_usarts
from spi_validator import validate_spi
from i2c_validator import validate_i2c
from adc_validator import validate_adc
from pwm_validator import validate_pwm
from timer_validator import validate_timers
from dma_validator import validate_dma
from systick_validator import validate_systick
from nvic_validator import validate_nvic


# --------------------------------------------------
# Read Live STM32 Status
# --------------------------------------------------

reader = STM32Reader()

try:
    rcc = validate_rcc(reader)
    gpio = validate_gpio(reader)
    usarts = validate_usarts(reader)
    spi = validate_spi(reader)
    i2c = validate_i2c(reader)
    adc = validate_adc(reader)
    pwm = validate_pwm(reader)
    timers = validate_timers(reader)
    dma = validate_dma(reader)
    systick = validate_systick(reader)
    nvic = validate_nvic(reader)
finally:
    reader.close()


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def is_nonzero_value(v):
    try:
        if isinstance(v, str):
            s = v.strip().upper()
            if s.startswith("0X"):
                return int(s, 16) != 0
            if s in ("PASS", "FAIL", "NOT_USED", "NOT USED", "-", ""):
                return False
            return float(s) != 0
        return int(v) != 0
    except:
        return False


def is_asserted(v):
    if isinstance(v, str):
        return v.strip().upper() in ("1", "YES", "TRUE", "PASS", "ENABLED")
    return v in (1, True)


# --------------------------------------------------
# USART status extraction
# --------------------------------------------------

u2 = usarts.get("USART2", {})

uart_enabled_raw = str(u2.get("Enabled", "NOT USED")).strip().upper()
uart_enabled = uart_enabled_raw in ("PASS", "1", "TRUE", "ENABLED", "YES")

uart_error = any([
    is_asserted(u2.get("Overrun", 0)),
    is_asserted(u2.get("FramingError", 0)),
    is_asserted(u2.get("ParityError", 0)),
    is_asserted(u2.get("NoiseError", 0)),
])

if uart_enabled:
    uart_status = "FAULT" if uart_error else "HEALTHY"
else:
    uart_status = "NOT USED"


# --------------------------------------------------
# Status extraction
# --------------------------------------------------

i2c_enabled = i2c.get("Enabled") == "PASS"
i2c_fault = (
    i2c_enabled and (
        i2c.get("BusError", 0) == 1 or
        i2c.get("AckFailure", 0) == 1 or
        i2c.get("ArbitrationLost", 0) == 1
    )
)

spi_enabled = spi.get("Enabled") == "PASS"
spi_fault = spi_enabled and spi.get("Overrun", 0) == 1

adc_enabled = adc.get("ADC Enabled") == "PASS"
adc_fault = adc_enabled and adc.get("ADC Value", 0) == 0

pwm_running = pwm.get("Timer Running") == "PASS"
pwm_fault = pwm.get("Timer Running") == "FAIL"

timer_used = any(is_nonzero_value(v) for v in timers.values())
gpio_used = any(is_nonzero_value(v) for v in gpio.values())

nvic_irq = bool(nvic.get("USART2_IRQ", 0))
nvic_fault = uart_enabled and not nvic_irq
nvic_used = uart_enabled

dma_fault = dma.get("DMA_ERROR", 0) != 0
dma_used = any(is_nonzero_value(v) for v in dma.values())

rcc_fault = rcc.get("GPIOA") != "PASS"


# --------------------------------------------------
# Convert Validation Results to AI Features
# --------------------------------------------------

data = {
    "UART":
        uart_status,

    "I2C":
        "HEALTHY" if i2c_enabled and not i2c_fault
        else "FAULT" if i2c_enabled and i2c_fault
        else "NOT USED",

    "SPI":
        "HEALTHY" if spi_enabled and not spi_fault
        else "FAULT" if spi_enabled and spi_fault
        else "NOT USED",

    "ADC":
        "HEALTHY" if adc_enabled and not adc_fault
        else "FAULT" if adc_enabled and adc_fault
        else "NOT USED",

    "PWM":
        "HEALTHY" if pwm_running
        else "FAULT" if pwm_fault
        else "NOT USED",

    "TIMER":
        "HEALTHY" if timer_used
        else "NOT USED",

    "NVIC":
        "HEALTHY" if nvic_used and not nvic_fault
        else "FAULT" if nvic_used and nvic_fault
        else "NOT USED",

    "DMA":
        "HEALTHY" if dma_used and not dma_fault
        else "FAULT" if dma_used and dma_fault
        else "NOT USED",

    "GPIO":
        "HEALTHY" if gpio_used
        else "NOT USED",

    "RCC":
        "HEALTHY" if not rcc_fault
        else "FAULT"
}


# --------------------------------------------------
# Load AI Model
# --------------------------------------------------

try:
    model = joblib.load("peripheral_health_model.pkl")
    sample = pd.DataFrame([data])
    prediction = model.predict(sample)[0]
except:
    prediction = "STM32F411RET6"


# --------------------------------------------------
# Health Score
# --------------------------------------------------

healthy_count = sum(1 for s in data.values() if s == "HEALTHY")
fault_count = sum(1 for s in data.values() if s == "FAULT")
not_used_count = sum(1 for s in data.values() if s == "NOT USED")

active_count = healthy_count + fault_count

if active_count == 0:
    health_score = 100
else:
    health_score = int((healthy_count * 100) / active_count)

total_peripherals = len(data)

if health_score >= 90:
    health_label = "EXCELLENT"
    health_color = "#4ade80"
elif health_score >= 70:
    health_label = "GOOD"
    health_color = "#4ade80"
elif health_score >= 50:
    health_label = "WARNING"
    health_color = "#facc15"
else:
    health_label = "CRITICAL"
    health_color = "#ef4444"

circumference = 339.3
dash_filled = round((health_score / 100) * circumference, 1)
dash_gap = round(circumference - dash_filled, 1)


# --------------------------------------------------
# Peripheral Status Rows
# --------------------------------------------------

PERI_ICONS = {
    "UART":  "&#x1F4E1;",
    "I2C":   "&#x1F517;",
    "SPI":   "&#x1F532;",
    "ADC":   "&#x223F;",
    "PWM":   "&#x223F;",
    "TIMER": "&#x23F0;",
    "NVIC":  "&#x1F514;",
    "DMA":   "&#x1F504;",
    "GPIO":  "&#x26A1;",
    "RCC":   "&#x23F0;",
}

peri_rows = ""
for peripheral, status in data.items():
    if status == "HEALTHY":
        badge = '<span class="badge-healthy">&#x2705; HEALTHY</span>'
    elif status == "FAULT":
        badge = '<span class="badge-fault">&#x274C; FAULT</span>'
    else:
        badge = '<span class="badge-unused">&#x26AA; NOT USED</span>'

    icon = PERI_ICONS.get(peripheral, "&#x2699;")
    peri_rows += f"""
        <tr>
            <td><span class="peri-name">{icon} {peripheral}</span></td>
            <td>{badge}</td>
        </tr>"""


# --------------------------------------------------
# Smart Fault Cards
# --------------------------------------------------

fault_cards_html = ""

if adc_enabled and adc.get("ADC Value", 0) == 0:
    fault_cards_html += """
        <div class="fault-card">
            <div class="fault-title"><span class="warn-icon">&#x26A0;</span> ADC Fault</div>
            <div class="fault-field"><span class="f-label">Reason</span><span class="f-val">ADC reading is zero</span></div>
            <div class="fault-field"><span class="f-label">Suggestion</span><span class="f-val">Check sensor power and analog input</span></div>
        </div>"""

if pwm_fault:
    fault_cards_html += """
        <div class="fault-card">
            <div class="fault-title"><span class="warn-icon">&#x26A0;</span> PWM Fault</div>
            <div class="fault-field"><span class="f-label">Reason</span><span class="f-val">Timer not running</span></div>
            <div class="fault-field"><span class="f-label">Suggestion</span><span class="f-val">Check timer enable and PWM configuration</span></div>
        </div>"""

if dma_used and dma_fault:
    fault_cards_html += """
        <div class="fault-card">
            <div class="fault-title"><span class="warn-icon">&#x26A0;</span> DMA Fault</div>
            <div class="fault-field"><span class="f-label">Reason</span><span class="f-val">DMA transfer error detected</span></div>
            <div class="fault-field"><span class="f-label">Suggestion</span><span class="f-val">Verify DMA stream, channel and memory configuration</span></div>
        </div>"""

if uart_enabled and not nvic_irq:
    fault_cards_html += """
        <div class="fault-card">
            <div class="fault-title"><span class="warn-icon">&#x26A0;</span> NVIC Fault</div>
            <div class="fault-field"><span class="f-label">Reason</span><span class="f-val">USART2 interrupt disabled</span></div>
            <div class="fault-field"><span class="f-label">Suggestion</span><span class="f-val">Enable USART2_IRQn interrupt in NVIC</span></div>
        </div>"""

if spi_enabled and spi.get("Overrun", 0) == 1:
    fault_cards_html += """
        <div class="fault-card">
            <div class="fault-title"><span class="warn-icon">&#x26A0;</span> SPI Fault</div>
            <div class="fault-field"><span class="f-label">Reason</span><span class="f-val">SPI receive overrun detected</span></div>
            <div class="fault-field"><span class="f-label">Suggestion</span><span class="f-val">Read SPI data before next transfer</span></div>
        </div>"""

if i2c_enabled and (
    i2c.get("BusError", 0) == 1 or
    i2c.get("AckFailure", 0) == 1 or
    i2c.get("ArbitrationLost", 0) == 1
):
    fault_cards_html += """
        <div class="fault-card">
            <div class="fault-title"><span class="warn-icon">&#x26A0;</span> I2C Fault</div>
            <div class="fault-field"><span class="f-label">Reason</span><span class="f-val">I2C communication error detected</span></div>
            <div class="fault-field"><span class="f-label">Suggestion</span><span class="f-val">Check SDA/SCL wiring and slave address</span></div>
        </div>"""

if uart_enabled and uart_error:
    reason = []

    if is_asserted(u2.get("Overrun", 0)):
        reason.append("Overrun error detected")
    if is_asserted(u2.get("FramingError", 0)):
        reason.append("Framing error detected")
    if is_asserted(u2.get("ParityError", 0)):
        reason.append("Parity error detected")
    if is_asserted(u2.get("NoiseError", 0)):
        reason.append("Noise error detected")

    reason_text = ", ".join(reason) if reason else "UART error detected"

    fault_cards_html += f"""
        <div class="fault-card">
            <div class="fault-title"><span class="warn-icon">&#x26A0;</span> UART Fault</div>
            <div class="fault-field"><span class="f-label">Reason</span><span class="f-val">{reason_text}</span></div>
            <div class="fault-field"><span class="f-label">Suggestion</span><span class="f-val">Check baud rate, serial frame format, and TX/RX wiring</span></div>
        </div>"""

if rcc_fault:
    fault_cards_html += """
        <div class="fault-card">
            <div class="fault-title"><span class="warn-icon">&#x26A0;</span> RCC Fault</div>
            <div class="fault-field"><span class="f-label">Reason</span><span class="f-val">Required peripheral clock is disabled</span></div>
            <div class="fault-field"><span class="f-label">Suggestion</span><span class="f-val">Enable peripheral clock in RCC register</span></div>
        </div>"""

if not fault_cards_html:
    fault_cards_html = """
        <div class="fault-ok">
            <span style="font-size:20px;">&#x2705;</span>
            <div>
                <div style="font-weight:700;color:#4ade80;margin-bottom:4px;">No Active Faults Detected</div>
                <div style="color:#64748b;font-size:12px;">All active peripherals operating normally.</div>
            </div>
        </div>"""


# --------------------------------------------------
# RCC rows
# --------------------------------------------------

rcc_rows = ""
for k, v in rcc.items():
    cls = "pass" if v == "PASS" else "fail" if v == "FAIL" else "val-num"
    rcc_rows += f'<div class="val-row"><span class="lbl">{k}</span><span class="{cls}">{v}</span></div>'


# --------------------------------------------------
# GPIO rows
# --------------------------------------------------

gpio_rows = ""
for k, v in gpio.items():
    gpio_rows += f'<div class="val-row"><span class="lbl">{k}</span><span class="val-hex">{v}</span></div>'


# --------------------------------------------------
# USART rows
# --------------------------------------------------

usart_rows = ""
for uart_name, uart_info in usarts.items():
    if uart_name == "USART2":
        uart_status_text = uart_status
    else:
        uart_status_text = uart_info.get("Status", uart_info.get("Enabled", "UNKNOWN"))

    uart_status_upper = str(uart_status_text).strip().upper()

    if uart_status_upper in ("HEALTHY", "PASS"):
        status_cls = "pass"
    elif uart_status_upper in ("FAULT", "FAIL"):
        status_cls = "fail"
    else:
        status_cls = "val-num"

    usart_rows += f'''
        <div class="val-row">
            <span class="lbl" style="font-weight:700;color:#60a5fa;">{uart_name}</span>
            <span class="{status_cls}">{uart_status_text}</span>
        </div>
    '''

    for key in ["TX", "RX", "Overrun", "ParityError", "FramingError", "NoiseError"]:
        val = uart_info.get(key, "-")

        if str(val).strip().upper() == "PASS":
            cls = "pass"
        elif str(val).strip().upper() in ("FAIL", "YES", "1", "TRUE"):
            cls = "fail"
        else:
            cls = "val-num"

        usart_rows += f'''
            <div class="val-row">
                <span class="lbl">{key}</span>
                <span class="{cls}">{val}</span>
            </div>
        '''


# --------------------------------------------------
# SPI rows
# --------------------------------------------------

spi_rows = ""
for k, v in spi.items():
    cls = "pass" if v == "PASS" else "fail" if v == "FAIL" else "val-num"
    spi_rows += f'<div class="val-row"><span class="lbl">{k}</span><span class="{cls}">{v}</span></div>'


# --------------------------------------------------
# I2C rows
# --------------------------------------------------

i2c_rows = ""
for k, v in i2c.items():
    cls = "pass" if v == "PASS" else "fail" if v == "FAIL" else "val-num"
    i2c_rows += f'<div class="val-row"><span class="lbl">{k}</span><span class="{cls}">{v}</span></div>'


# --------------------------------------------------
# ADC rows
# --------------------------------------------------

adc_rows = ""
for k, v in adc.items():
    cls = "pass" if v == "PASS" else "fail" if v == "FAIL" else "val-num"
    adc_rows += f'<div class="val-row"><span class="lbl">{k}</span><span class="{cls}">{v}</span></div>'


# --------------------------------------------------
# PWM rows
# --------------------------------------------------

pwm_rows = ""
for k, v in pwm.items():
    cls = "pass" if v == "PASS" else "fail" if v == "FAIL" else "val-num"
    pwm_rows += f'<div class="val-row"><span class="lbl">{k}</span><span class="{cls}">{v}</span></div>'


# --------------------------------------------------
# Timer rows
# --------------------------------------------------

timer_rows = ""
for k, v in timers.items():
    timer_rows += f'<div class="val-row"><span class="lbl">{k}</span><span class="val-num">{v}</span></div>'


# --------------------------------------------------
# DMA rows
# --------------------------------------------------

dma_rows = ""
for k, v in dma.items():
    dma_rows += f'<div class="val-row"><span class="lbl">{k}</span><span class="val-num">{v}</span></div>'


# --------------------------------------------------
# SysTick rows
# --------------------------------------------------

systick_rows = ""
for k, v in systick.items():
    cls = "pass" if v == "PASS" else "fail" if v == "FAIL" else "val-num"
    systick_rows += f'<div class="val-row"><span class="lbl">{k}</span><span class="{cls}">{v}</span></div>'


# --------------------------------------------------
# NVIC pills
# --------------------------------------------------

nvic_pills = ""
for k, v in nvic.items():
    color = "#4ade80" if v else "#ef4444"
    nvic_pills += f'<div class="nvic-pill">{k} : <span style="color:{color};font-weight:700;">{v}</span></div>'


# --------------------------------------------------
# HTML Dashboard
# --------------------------------------------------

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>STM32F411RET6 AI Dashboard</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}

body {{
    background:#080d1a;
    color:#e2e8f0;
    font-family:'Segoe UI', system-ui, sans-serif;
    font-size:13px;
    min-height:100vh;
}}

.header {{
    background:#0b1120;
    border-bottom:2px solid #1e3a5f;
    padding:14px 28px;
    display:flex;
    align-items:center;
    justify-content:space-between;
}}

.header-left {{ display:flex; align-items:center; gap:18px; }}

.chip-box {{
    width:60px; height:60px;
    border:2px solid #2563eb;
    border-radius:8px;
    background:#0f172a;
    display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    gap:3px;
    position:relative;
}}

.chip-box::before {{
    content:'';
    position:absolute;
    inset:5px;
    border:1px solid #1d4ed8;
    border-radius:3px;
}}

.chip-dots {{
    display:flex; gap:2px;
}}

.chip-dot {{
    width:4px; height:4px;
    background:#1d4ed8;
    border-radius:1px;
}}

.chip-text {{
    font-size:10px; font-weight:800;
    color:#60a5fa; letter-spacing:1px;
    z-index:1;
}}

.title h1 {{
    font-size:24px; font-weight:700;
    color:#f1f5f9; letter-spacing:0.3px;
}}

.title h1 span {{ color:#3b82f6; }}

.header-right {{ display:flex; gap:14px; }}

.meta-pill {{
    background:#0f172a;
    border:1px solid #1e3a5f;
    border-radius:20px;
    padding:6px 16px;
    font-size:12px; color:#94a3b8;
    display:flex; align-items:center; gap:8px;
}}

.meta-pill .dot {{
    width:7px; height:7px;
    border-radius:50%;
}}

.main {{
    display:grid;
    grid-template-columns:1fr 390px;
    gap:14px;
    padding:14px;
}}

.left {{ display:flex; flex-direction:column; gap:14px; }}
.right {{ display:flex; flex-direction:column; gap:14px; }}

.card {{
    background:#0b1120;
    border:1px solid #1a2d48;
    border-radius:10px;
    overflow:hidden;
}}

.card-hdr {{
    display:flex; align-items:center; gap:8px;
    padding:9px 14px;
    border-bottom:1px solid #1a2d48;
    font-size:11px; font-weight:700;
    letter-spacing:1px; text-transform:uppercase;
    color:#64748b;
}}

.card-hdr-icon {{
    width:22px; height:22px; border-radius:5px;
    display:flex; align-items:center; justify-content:center;
    font-size:12px;
}}

.hdr-blue {{ background:#1e3a5f; color:#60a5fa; }}
.hdr-red {{ background:#2a0f0f; color:#f87171; }}

.val-grid {{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
    padding:12px;
}}

.vblock {{
    background:#0f1923;
    border:1px solid #1a2d48;
    border-radius:8px;
    padding:10px 12px;
}}

.vblock h4 {{
    font-size:11px; font-weight:700;
    letter-spacing:0.8px; text-transform:uppercase;
    margin-bottom:8px;
    display:flex; align-items:center; gap:6px;
}}

.h4-blue {{ color:#60a5fa; }}
.h4-green {{ color:#4ade80; }}
.h4-purple {{ color:#a78bfa; }}
.h4-cyan {{ color:#22d3ee; }}
.h4-orange {{ color:#fb923c; }}
.h4-yellow {{ color:#facc15; }}
.h4-red {{ color:#f87171; }}
.h4-teal {{ color:#2dd4bf; }}

.val-row {{
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:3px 0;
    border-bottom:1px solid #131e2e;
    font-size:12px;
}}

.val-row:last-child {{ border-bottom:none; }}

.lbl {{ color:#64748b; }}
.pass {{ color:#4ade80; font-weight:700; }}
.fail {{ color:#ef4444; font-weight:700; }}
.val-num {{ color:#cbd5e1; }}
.val-hex {{ color:#a78bfa; font-family:Consolas,monospace; font-size:11px; }}

.nvic-pills {{
    display:flex; flex-wrap:wrap; gap:8px;
    padding:10px 12px;
}}

.nvic-pill {{
    background:#0f1923;
    border:1px solid #1a2d48;
    border-radius:6px;
    padding:5px 12px;
    font-size:12px; color:#94a3b8;
}}

.health-card {{
    background:#0b1120;
    border:1px solid #1a2d48;
    border-radius:10px;
    padding:16px;
}}

.health-hdr {{
    display:flex; align-items:center; gap:8px;
    font-size:11px; font-weight:700;
    letter-spacing:1px; text-transform:uppercase;
    color:#64748b; margin-bottom:14px;
}}

.score-wrap {{ display:flex; align-items:center; gap:20px; }}

.donut-wrap {{
    position:relative; width:110px; height:110px; flex-shrink:0;
}}

.donut-wrap svg {{
    width:100%; height:100%;
    transform:rotate(-90deg);
}}

.donut-center {{
    position:absolute; inset:0;
    display:flex; flex-direction:column;
    align-items:center; justify-content:center;
}}

.donut-pct {{
    font-size:26px; font-weight:800;
    line-height:1;
    color:{health_color};
}}

.donut-lbl {{
    font-size:10px; font-weight:700;
    letter-spacing:1px; margin-top:2px;
    color:{health_color};
}}

.legend {{ flex:1; }}

.legend-row {{
    display:flex; align-items:center;
    justify-content:space-between;
    padding:7px 0;
    border-bottom:1px solid #111827;
    font-size:13px;
}}

.legend-row:last-child {{ border-bottom:none; }}

.leg-left {{ display:flex; align-items:center; gap:10px; }}

.leg-dot {{
    width:20px; height:20px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:11px;
}}

.leg-green {{ background:#14291f; color:#4ade80; }}
.leg-red {{ background:#2a0f0f; color:#ef4444; }}
.leg-gray {{ background:#1a2535; color:#64748b; }}

.leg-name {{ color:#94a3b8; font-weight:500; }}
.leg-count {{ font-size:17px; font-weight:800; }}
.lc-green {{ color:#4ade80; }}
.lc-red {{ color:#ef4444; }}
.lc-gray {{ color:#64748b; }}

.total-bar {{
    display:flex; justify-content:space-between;
    padding:8px 0 0;
    margin-top:6px;
    border-top:1px solid #1a2d48;
    font-size:11px;
    color:#64748b;
    text-transform:uppercase; letter-spacing:0.5px;
}}

.peri-table {{ width:100%; border-collapse:collapse; }}

.peri-table th {{
    padding:8px 14px;
    text-align:left;
    font-size:11px; font-weight:600;
    text-transform:uppercase; letter-spacing:0.5px;
    color:#64748b;
    border-bottom:1px solid #1a2d48;
}}

.peri-table td {{
    padding:7px 14px;
    border-bottom:1px solid #0f1923;
    font-size:13px;
}}

.peri-table tr:last-child td {{ border-bottom:none; }}

.peri-name {{ color:#94a3b8; }}

.badge-healthy {{ color:#4ade80; font-weight:700; }}
.badge-fault {{ color:#ef4444; font-weight:700; }}
.badge-unused {{ color:#64748b; font-weight:600; }}

.fault-grid {{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
    padding:12px;
}}

.fault-card {{
    background:#150d0d;
    border:1px solid #7f1d1d;
    border-radius:8px;
    padding:12px;
}}

.fault-title {{
    display:flex; align-items:center; gap:6px;
    font-size:13px; font-weight:700;
    color:#fca5a5; margin-bottom:10px;
}}

.warn-icon {{ color:#f87171; font-size:15px; }}

.fault-field {{ margin-bottom:7px; }}

.f-label {{
    display:block;
    font-size:10px; text-transform:uppercase;
    letter-spacing:0.5px; color:#64748b;
    margin-bottom:2px;
}}

.f-val {{ font-size:12px; color:#cbd5e1; }}

.fault-ok {{
    grid-column:1/-1;
    background:#0b1f12;
    border:1px solid #166534;
    border-radius:8px;
    padding:16px;
    display:flex; align-items:center; gap:14px;
}}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <div class="chip-box">
      <div class="chip-dots">
        <div class="chip-dot"></div><div class="chip-dot"></div>
        <div class="chip-dot"></div><div class="chip-dot"></div>
      </div>
      <div class="chip-text">STM32</div>
      <div class="chip-dots">
        <div class="chip-dot"></div><div class="chip-dot"></div>
        <div class="chip-dot"></div><div class="chip-dot"></div>
      </div>
    </div>
    <div class="title">
      <h1>STM32F411RET6 <span>AI</span> PERIPHERAL HEALTH DASHBOARD</h1>
    </div>
  </div>
  <div class="header-right">
    <div class="meta-pill">
      <div class="dot" style="background:#3b82f6;"></div>
      &#128197; Generated : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </div>
    <div class="meta-pill">
      <div class="dot" style="background:#4ade80;"></div>
      &#9881; MCU : {prediction}
    </div>
  </div>
</div>

<div class="main">
  <div class="left">
    <div class="card">
      <div class="card-hdr">
        <div class="card-hdr-icon hdr-blue">&#128203;</div>
        VALIDATION REPORT
      </div>

      <div class="val-grid">
        <div class="vblock">
          <h4 class="h4-blue">&#128336; RCC STATUS</h4>
          {rcc_rows}
        </div>

        <div class="vblock">
          <h4 class="h4-purple">&#9889; GPIO STATUS</h4>
          {gpio_rows}
        </div>

        <div class="vblock">
          <h4 class="h4-green">&#128225; USART STATUS</h4>
          {usart_rows}
        </div>

        <div class="vblock">
          <h4 class="h4-cyan">&#128306; SPI STATUS</h4>
          {spi_rows}
        </div>

        <div class="vblock">
          <h4 class="h4-teal">&#128279; I2C STATUS</h4>
          {i2c_rows}
        </div>

        <div class="vblock">
          <h4 class="h4-red">&#12316; ADC STATUS</h4>
          {adc_rows}
        </div>

        <div class="vblock">
          <h4 class="h4-orange">&#12316; PWM STATUS</h4>
          {pwm_rows}
        </div>

        <div class="vblock">
          <h4 class="h4-blue">&#128336; TIMER STATUS</h4>
          {timer_rows}
        </div>

        <div class="vblock">
          <h4 class="h4-cyan">&#128260; DMA STATUS</h4>
          {dma_rows}
        </div>

        <div class="vblock">
          <h4 class="h4-yellow">&#128336; SYSTICK STATUS</h4>
          {systick_rows}
        </div>
      </div>

      <div class="vblock" style="margin:0 12px 12px;">
        <h4 class="h4-yellow">&#128276; NVIC STATUS</h4>
        <div class="nvic-pills">
          {nvic_pills}
        </div>
      </div>
    </div>
  </div>

  <div class="right">
    <div class="health-card">
      <div class="health-hdr">
        &#9829; HEALTH SCORE
      </div>
      <div class="score-wrap">
        <div class="donut-wrap">
          <svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
            <circle cx="60" cy="60" r="54" fill="none" stroke="#1a2535" stroke-width="10"/>
            <circle cx="60" cy="60" r="54" fill="none"
              stroke="{health_color}" stroke-width="10"
              stroke-linecap="round"
              stroke-dasharray="{dash_filled} {dash_gap}"/>
          </svg>
          <div class="donut-center">
            <div class="donut-pct">{health_score}%</div>
            <div class="donut-lbl">{health_label}</div>
          </div>
        </div>
        <div class="legend">
          <div class="legend-row">
            <div class="leg-left">
              <div class="leg-dot leg-green">&#10003;</div>
              <span class="leg-name">HEALTHY</span>
            </div>
            <span class="leg-count lc-green">{healthy_count}</span>
          </div>
          <div class="legend-row">
            <div class="leg-left">
              <div class="leg-dot leg-red">&#10007;</div>
              <span class="leg-name">FAULT</span>
            </div>
            <span class="leg-count lc-red">{fault_count}</span>
          </div>
          <div class="legend-row">
            <div class="leg-left">
              <div class="leg-dot leg-gray">&#8211;</div>
              <span class="leg-name">NOT USED</span>
            </div>
            <span class="leg-count lc-gray">{not_used_count}</span>
          </div>
          <div class="total-bar">
            <span>TOTAL PERIPHERALS</span>
            <span style="color:#e2e8f0;font-weight:700;">{total_peripherals}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-hdr">
        <div class="card-hdr-icon hdr-blue">&#9776;</div>
        PERIPHERAL STATUS
      </div>
      <table class="peri-table">
        <thead>
          <tr>
            <th>Peripheral</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {peri_rows}
        </tbody>
      </table>
    </div>

    <div class="card">
      <div class="card-hdr">
        <div class="card-hdr-icon hdr-red">&#9888;</div>
        FAULT ANALYSIS
      </div>
      <div class="fault-grid">
        {fault_cards_html}
      </div>
    </div>
  </div>
</div>

</body>
</html>"""


# --------------------------------------------------
# Save Dashboard
# --------------------------------------------------

with open("health_report.html", "w", encoding="utf-8") as f:
    f.write(html)

webbrowser.open("health_report.html")
print("Health Report Generated Successfully")