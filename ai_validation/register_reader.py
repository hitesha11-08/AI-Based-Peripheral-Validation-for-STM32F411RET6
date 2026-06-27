from pyocd.core.helpers import ConnectHelper

class STM32Reader:

    def __init__(self):
        self.session = ConnectHelper.session_with_chosen_probe(
            target_override="cortex_m"
        )

        self.session.open()
        self.target = self.session.target

    def read32(self, address):
        return self.target.read32(address)

    def close(self):
        self.session.close()