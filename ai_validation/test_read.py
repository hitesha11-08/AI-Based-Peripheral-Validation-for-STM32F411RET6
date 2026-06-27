from register_reader import STM32Reader

reader = STM32Reader()

rcc_ahb1enr = reader.read32(0x40023830)

print("RCC_AHB1ENR =", hex(rcc_ahb1enr))

reader.close()