# UPI App Entry Point
from upi.upi_transactions import main as upi_main

if __name__ == "__main__":
    print("UPI app starting with SBI PhonePe-style GUI...")
    # TODO: Launch SBI PhonePe-style GUI for UPI operations
    # Example: from gui.phonepe_upi import launch_phonepe_upi_gui
    # launch_phonepe_upi_gui()
    upi_main()
