import usb.core
import usb.util
import time
from auth_broker import badgeRead


class CardReader():
    def __init__(self):
        # CONFIG
        # Change VENDOR_ID and PRODUCT_ID corresponding to a reader model
        # JRK - changed PROX_END to 4 to accommodate the reader config I use
        # RFID reader config = no stripping of leading or trailing digits.
        self.VENDOR_ID = 0x0C27
        self.PRODUCT_ID = 0x3BFA
        self.PROX_END = 4
        self.INTERFACE = 0
        # END CONFIG
        # Detect the device
        self.dev = usb.core.find(idVendor=self.VENDOR_ID,
                                 idProduct=self.PRODUCT_ID)
        if self.dev is None:
            # raise ValueError('Card reader is not connected')
            self.connected = False

        else:
            # Make sure libusb handles the device
            self.connected = True
            # print(self.dev)
            if self.dev.is_kernel_driver_active(self.INTERFACE):
                print('Detach Kernel Driver')
                self.dev.detach_kernel_driver(self.INTERFACE)
            # Set a mode
            # ctrl_transfer is used to control endpoint0
            self.dev.set_configuration(1)
            usb.util.claim_interface(self.dev, self.INTERFACE)
            self.dev.ctrl_transfer(0x21, 9, 0x0300, 0, [0x008d])

        self.badge_hex = None
        self.badge_fac = 0
        self.badge_num = 0

    def read_card(self):
        # Pull the status
        if self.dev is None:
            print('reader disconected')
            return False
        else:
            output = self.dev.ctrl_transfer(0xA1, 1, 0x0300, 0, self.PROX_END)
            if output[0] > 0:
                self.badge_hex = self._decode_card(output)
                '''
                Get Facility Access Code by slicing the first 8 binary digits &
                converting to integer. Get Card ID Number by converting the
                last 16 digits to integer
                '''
                self.badge_fac = \
                    self._bin_to_int(bin(int(self.badge_hex, 16))[4:-1][:7])
                self.badge_num = \
                    self._bin_to_int(bin(int(self.badge_hex, 16))[4:-1][-16:])
                return True

    def read_card_loop(self, launch=False):
        last_read = '0x0000'
        while self.read_card():
            if self.badge_hex != last_read and self.badge_hex != '0x0000':
                time.sleep(0.3)
                last_read = self.badge_hex
                print(self.badge_hex)
                print(str(self.badge_num))
                if launch is True:
                    badgeRead(self.badge_hex, self.badge_num)

    def _bin_to_int(self, binary):
        decimal = 0
        for digit in binary:
            decimal = decimal*2 + int(digit)
        return decimal

    # Convert output into integers
    def _decode_card(self, raw_card_read):
        proxHex = '0x'
        for h in (reversed(raw_card_read)):
            # JRK - added if stmt to handle 1-digit numbers without leading 0
            if (h < 16 and h > 0):
                proxHex += '0' + hex(h)[2:]
            else:
                proxHex += hex(h)[2:]
        # Get 24-digit binary (slice first 2 and last 1 digit from the binary)
        return proxHex
