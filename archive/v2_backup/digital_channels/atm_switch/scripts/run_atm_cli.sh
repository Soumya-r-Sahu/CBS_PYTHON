#!/bin/bash
# Run ATM CLI Interface for CBS_PYTHON

echo "Starting ATM CLI Interface..."
echo ""

# Set Python path to include project root
export PYTHONPATH=$PYTHONPATH:$(dirname $(dirname $(dirname $(dirname $(realpath $0)))))

# Run the ATM CLI interface
python -m digital_channels.atm-switch.presentation.cli.atm_interface

echo ""
echo "ATM CLI Interface closed."
