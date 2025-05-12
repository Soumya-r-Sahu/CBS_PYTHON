# ATM App Entry Point
from app.atm.atm_interface import AtmInterface

if __name__ == "__main__":
    atm = AtmInterface()
    atm.start()
