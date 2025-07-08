"""
Derivatives management package for treasury operations.

This package provides functionality for managing derivative financial instruments,
including options, futures, swaps, and other derivative contracts.
"""

from pathlib import Path
import os
import sys

# Add current directory to path to ensure local imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


# Import modules
from treasury.derivatives.options_pricing import (
    Option, OptionType, OptionStyle, 
    BlackScholes, BinomialTreeModel
)

from treasury.derivatives.swap_operations import (
    SwapContract, SwapLeg, SwapType, SwapManager,
    PaymentFrequency, DayCountConvention, SwapPricingModel
)

from treasury.derivatives.futures_management import (
    FuturesContract, FuturesPosition, FuturesType,
    MarginType, MarginCall, FuturesManager
)

from treasury.derivatives.derivatives_risk import (
    DerivativesRiskManager, DerivativePosition, 
    RiskMetricType, StressTestLevel, RiskLimit, RiskReport
)

__all__ = [
    # Options
    'Option', 'OptionType', 'OptionStyle', 'BlackScholes', 'BinomialTreeModel',
    
    # Swaps
    'SwapContract', 'SwapLeg', 'SwapType', 'SwapManager',
    'PaymentFrequency', 'DayCountConvention', 'SwapPricingModel',
    
    # Futures
    'FuturesContract', 'FuturesPosition', 'FuturesType',
    'MarginType', 'MarginCall', 'FuturesManager',
    
    # Risk Management
    'DerivativesRiskManager', 'DerivativePosition',
    'RiskMetricType', 'StressTestLevel', 'RiskLimit', 'RiskReport'
]