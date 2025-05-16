"""
Options pricing module for treasury operations.

This module provides functionality for pricing and valuing options contracts,
including implementations of Black-Scholes and binomial pricing models.
"""

import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union, Callable
from decimal import Decimal
import logging
import math
import numpy as np
from scipy import stats

# Configure logging
logger = logging.getLogger(__name__)


class OptionType(Enum):
    """Option types."""
    CALL = "call"
    PUT = "put"


class OptionStyle(Enum):
    """Option exercise styles."""
    EUROPEAN = "european"  # Can only be exercised at expiration
    AMERICAN = "american"  # Can be exercised any time before expiration
    BERMUDAN = "bermudan"  # Can be exercised on specific dates


@dataclass
class Option:
    """Represents an option contract."""
    
    id: str
    underlying: str  # Ticker or identifier of underlying asset
    option_type: OptionType
    style: OptionStyle
    strike_price: Decimal
    expiry_date: datetime.date
    contract_size: int = 1
    currency: str = "USD"
    
    @property
    def is_call(self) -> bool:
        """Check if option is a call option."""
        return self.option_type == OptionType.CALL
    
    @property
    def is_put(self) -> bool:
        """Check if option is a put option."""
        return self.option_type == OptionType.PUT
    
    @property
    def days_to_expiry(self) -> int:
        """Calculate days until expiration."""
        return max(0, (self.expiry_date - datetime.date.today()).days)
    
    @property
    def years_to_expiry(self) -> float:
        """Calculate years until expiration."""
        return self.days_to_expiry / 365.0


class BlackScholes:
    """
    Black-Scholes option pricing model.
    
    This class implements the Black-Scholes model for pricing
    European call and put options.
    """
    
    @staticmethod
    def price_option(
        option: Option,
        spot_price: float,
        risk_free_rate: float,
        volatility: float,
        dividend_yield: float = 0.0
    ) -> Dict[str, float]:
        """
        Price an option using the Black-Scholes model.
        
        Args:
            option: Option contract
            spot_price: Current price of the underlying asset
            risk_free_rate: Risk-free interest rate (as a decimal, e.g., 0.05 for 5%)
            volatility: Implied volatility of the underlying asset (as a decimal)
            dividend_yield: Dividend yield of the underlying asset (as a decimal)
            
        Returns:
            Dictionary containing price and Greeks
        """
        if option.style != OptionStyle.EUROPEAN:
            logger.warning("Black-Scholes model is designed for European options")
        
        # Extract parameters
        S = spot_price
        K = float(option.strike_price)
        T = option.years_to_expiry
        r = risk_free_rate
        q = dividend_yield
        sigma = volatility
        
        # Handle expired options
        if T <= 0:
            if option.is_call:
                price = max(0, S - K)
            else:
                price = max(0, K - S)
                
            return {
                "price": price,
                "delta": 1.0 if price > 0 else 0.0 if option.is_call else -1.0 if price > 0 else 0.0,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0,
                "rho": 0.0
            }
        
        # Calculate d1 and d2
        d1 = (math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        # Calculate option price
        if option.is_call:
            price = S * math.exp(-q * T) * stats.norm.cdf(d1) - K * math.exp(-r * T) * stats.norm.cdf(d2)
        else:
            price = K * math.exp(-r * T) * stats.norm.cdf(-d2) - S * math.exp(-q * T) * stats.norm.cdf(-d1)
        
        # Calculate Greeks
        delta = BlackScholes._calculate_delta(option, S, K, T, r, q, sigma, d1)
        gamma = BlackScholes._calculate_gamma(S, T, sigma, d1)
        theta = BlackScholes._calculate_theta(option, S, K, T, r, q, sigma, d1, d2)
        vega = BlackScholes._calculate_vega(S, T, sigma, d1)
        rho = BlackScholes._calculate_rho(option, K, T, r, d2)
        
        # Adjust for contract size
        price *= option.contract_size
        delta *= option.contract_size
        gamma *= option.contract_size
        theta *= option.contract_size
        vega *= option.contract_size
        rho *= option.contract_size
        
        return {
            "price": price,
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "rho": rho
        }
    
    @staticmethod
    def _calculate_delta(
        option: Option,
        S: float,
        K: float,
        T: float,
        r: float,
        q: float,
        sigma: float,
        d1: float
    ) -> float:
        """Calculate Delta - rate of change of option price with respect to underlying price."""
        if option.is_call:
            return math.exp(-q * T) * stats.norm.cdf(d1)
        else:
            return math.exp(-q * T) * (stats.norm.cdf(d1) - 1)
    
    @staticmethod
    def _calculate_gamma(
        S: float,
        T: float,
        sigma: float,
        d1: float
    ) -> float:
        """Calculate Gamma - rate of change of Delta with respect to underlying price."""
        return math.exp(-0 * T) * stats.norm.pdf(d1) / (S * sigma * math.sqrt(T))
    
    @staticmethod
    def _calculate_theta(
        option: Option,
        S: float,
        K: float,
        T: float,
        r: float,
        q: float,
        sigma: float,
        d1: float,
        d2: float
    ) -> float:
        """Calculate Theta - rate of change of option price with respect to time."""
        term1 = -S * math.exp(-q * T) * stats.norm.pdf(d1) * sigma / (2 * math.sqrt(T))
        
        if option.is_call:
            term2 = -r * K * math.exp(-r * T) * stats.norm.cdf(d2)
            term3 = q * S * math.exp(-q * T) * stats.norm.cdf(d1)
        else:
            term2 = r * K * math.exp(-r * T) * stats.norm.cdf(-d2)
            term3 = -q * S * math.exp(-q * T) * stats.norm.cdf(-d1)
            
        # Convert from annual to daily theta
        return (term1 + term2 + term3) / 365.0
    
    @staticmethod
    def _calculate_vega(
        S: float,
        T: float,
        sigma: float,
        d1: float
    ) -> float:
        """Calculate Vega - rate of change of option price with respect to volatility."""
        return S * math.sqrt(T) * stats.norm.pdf(d1) * 0.01  # Scaled for 1% change
    
    @staticmethod
    def _calculate_rho(
        option: Option,
        K: float,
        T: float,
        r: float,
        d2: float
    ) -> float:
        """Calculate Rho - rate of change of option price with respect to interest rate."""
        if option.is_call:
            return K * T * math.exp(-r * T) * stats.norm.cdf(d2) * 0.01  # Scaled for 1% change
        else:
            return -K * T * math.exp(-r * T) * stats.norm.cdf(-d2) * 0.01  # Scaled for 1% change
    
    @staticmethod
    def implied_volatility(
        option: Option,
        spot_price: float,
        risk_free_rate: float,
        option_price: float,
        dividend_yield: float = 0.0,
        precision: float = 0.0001,
        max_iterations: int = 100
    ) -> float:
        """
        Calculate implied volatility using numerical methods.
        
        Args:
            option: Option contract
            spot_price: Current price of the underlying asset
            risk_free_rate: Risk-free interest rate
            option_price: Market price of the option
            dividend_yield: Dividend yield
            precision: Required precision
            max_iterations: Maximum number of iterations
            
        Returns:
            Implied volatility or None if calculation fails
        """
        # Initial guess
        sigma_low = 0.001
        sigma_high = 5.0
        
        # Price at low volatility
        price_low = BlackScholes.price_option(
            option, spot_price, risk_free_rate, sigma_low, dividend_yield
        )["price"]
        
        # Price at high volatility
        price_high = BlackScholes.price_option(
            option, spot_price, risk_free_rate, sigma_high, dividend_yield
        )["price"]
        
        # Check if market price is in range
        if option_price <= price_low:
            return sigma_low
        if option_price >= price_high:
            return sigma_high
            
        # Binary search
        for _ in range(max_iterations):
            sigma_mid = (sigma_low + sigma_high) / 2.0
            price_mid = BlackScholes.price_option(
                option, spot_price, risk_free_rate, sigma_mid, dividend_yield
            )["price"]
            
            if abs(price_mid - option_price) < precision:
                return sigma_mid
                
            if price_mid < option_price:
                sigma_low = sigma_mid
            else:
                sigma_high = sigma_mid
                
        # Return best estimate if max iterations reached
        return (sigma_low + sigma_high) / 2.0


class BinomialTree:
    """
    Binomial option pricing model.
    
    This class implements the Cox-Ross-Rubinstein (CRR) binomial tree model
    for pricing American and European options.
    """
    
    @staticmethod
    def price_option(
        option: Option,
        spot_price: float,
        risk_free_rate: float,
        volatility: float,
        dividend_yield: float = 0.0,
        steps: int = 50
    ) -> Dict[str, float]:
        """
        Price an option using the binomial tree model.
        
        Args:
            option: Option contract
            spot_price: Current price of the underlying asset
            risk_free_rate: Risk-free interest rate (as a decimal)
            volatility: Implied volatility of the underlying asset (as a decimal)
            dividend_yield: Dividend yield of the underlying asset (as a decimal)
            steps: Number of time steps in the tree
            
        Returns:
            Dictionary containing price and Greeks
        """
        # Extract parameters
        S = spot_price
        K = float(option.strike_price)
        T = option.years_to_expiry
        r = risk_free_rate
        q = dividend_yield
        sigma = volatility
        n = steps
        
        # Handle expired options
        if T <= 0:
            if option.is_call:
                price = max(0, S - K)
            else:
                price = max(0, K - S)
                
            return {
                "price": price,
                "delta": 1.0 if price > 0 else 0.0 if option.is_call else -1.0 if price > 0 else 0.0,
                "gamma": 0.0,
                "theta": 0.0
            }
        
        # Calculate tree parameters
        dt = T / n
        u = math.exp(sigma * math.sqrt(dt))
        d = 1 / u
        p = (math.exp((r - q) * dt) - d) / (u - d)
        
        # Initialize arrays for stock prices and option values
        stock_prices = np.zeros((n+1, n+1))
        option_values = np.zeros((n+1, n+1))
        
        # Build stock price tree
        for i in range(n + 1):
            for j in range(i + 1):
                stock_prices[j, i] = S * (u ** (i - j)) * (d ** j)
        
        # Calculate option values at expiration
        for j in range(n + 1):
            if option.is_call:
                option_values[j, n] = max(0, stock_prices[j, n] - K)
            else:
                option_values[j, n] = max(0, K - stock_prices[j, n])
        
        # Backward induction
        discount = math.exp(-r * dt)
        for i in range(n - 1, -1, -1):
            for j in range(i + 1):
                # Expected value from binomial model
                expected_value = p * option_values[j, i+1] + (1-p) * option_values[j+1, i+1]
                option_values[j, i] = discount * expected_value
                
                # For American options, check if early exercise is optimal
                if option.style == OptionStyle.AMERICAN:
                    if option.is_call:
                        early_exercise = max(0, stock_prices[j, i] - K)
                    else:
                        early_exercise = max(0, K - stock_prices[j, i])
                        
                    option_values[j, i] = max(option_values[j, i], early_exercise)
        
        # Calculate price and Greeks
        price = option_values[0, 0]
        
        # Calculate delta
        if n > 1:
            delta = (option_values[0, 1] - option_values[1, 1]) / (stock_prices[0, 1] - stock_prices[1, 1])
        else:
            delta = 0
            
        # Calculate gamma
        if n > 2:
            delta_up = (option_values[0, 2] - option_values[1, 2]) / (stock_prices[0, 2] - stock_prices[1, 2])
            delta_down = (option_values[1, 2] - option_values[2, 2]) / (stock_prices[1, 2] - stock_prices[2, 2])
            gamma = (delta_up - delta_down) / (0.5 * (stock_prices[0, 2] - stock_prices[2, 2]))
        else:
            gamma = 0
            
        # Calculate theta (approximate)
        if n > 1:
            theta = (option_values[0, 1] - option_values[0, 0]) / dt / 365.0  # Convert to daily
        else:
            theta = 0
            
        # Adjust for contract size
        price *= option.contract_size
        delta *= option.contract_size
        gamma *= option.contract_size
        theta *= option.contract_size
        
        return {
            "price": price,
            "delta": delta,
            "gamma": gamma,
            "theta": theta
        }


# Example usage
if __name__ == "__main__":
    # Create a sample option
    today = datetime.date.today()
    expiry = today + datetime.timedelta(days=30)
    
    call_option = Option(
        id="AAPL_C_150",
        underlying="AAPL",
        option_type=OptionType.CALL,
        style=OptionStyle.EUROPEAN,
        strike_price=Decimal("150"),
        expiry_date=expiry,
        contract_size=100,
        currency="USD"
    )
    
    put_option = Option(
        id="AAPL_P_150",
        underlying="AAPL",
        option_type=OptionType.PUT,
        style=OptionStyle.AMERICAN,
        strike_price=Decimal("150"),
        expiry_date=expiry,
        contract_size=100,
        currency="USD"
    )
    
    # Set market parameters
    spot_price = 155.0
    risk_free_rate = 0.03  # 3%
    volatility = 0.25      # 25%
    dividend_yield = 0.005 # 0.5%
    
    # Price options using Black-Scholes
    bs_call = BlackScholes.price_option(
        call_option, spot_price, risk_free_rate, volatility, dividend_yield
    )
    
    print(f"Black-Scholes Call Price: ${bs_call['price']:.2f}")
    print(f"Delta: {bs_call['delta']:.4f}")
    print(f"Gamma: {bs_call['gamma']:.4f}")
    print(f"Theta: ${bs_call['theta']:.4f}/day")
    print(f"Vega: ${bs_call['vega']:.4f} per 1% vol")
    print(f"Rho: ${bs_call['rho']:.4f} per 1% rate")
    
    # Price options using Binomial Tree
    bin_call = BinomialTree.price_option(
        call_option, spot_price, risk_free_rate, volatility, dividend_yield, steps=100
    )
    
    bin_put = BinomialTree.price_option(
        put_option, spot_price, risk_free_rate, volatility, dividend_yield, steps=100
    )
    
    print(f"\nBinomial Tree Call Price: ${bin_call['price']:.2f}")
    print(f"Binomial Tree Put Price: ${bin_put['price']:.2f}")
    
    # Calculate implied volatility
    option_market_price = 8.75  # Example market price
    implied_vol = BlackScholes.implied_volatility(
        call_option, spot_price, risk_free_rate, option_market_price, dividend_yield
    )
    
    print(f"\nImplied Volatility: {implied_vol:.2%}")
