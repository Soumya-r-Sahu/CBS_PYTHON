# ATM App Entry Point
from .atm_interface import AtmInterface


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
if __name__ == "__main__":
    atm = AtmInterface()
    atm.start()
