"""
Forex Risk module for treasury operations.

This module provides functionality for assessing and managing foreign exchange risk,
including position monitoring, risk metrics calculation, and stress testing.
"""

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union, Tuple, Any
from decimal import Decimal
import logging
import math
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

# Configure logging
logger = logging.getLogger(__name__)


class RiskMetricType(Enum):
    """Types of risk metrics."""
    VAR = "value_at_risk"
    EXPECTED_SHORTFALL = "expected_shortfall"
    VOLATILITY = "volatility"
    CORRELATION = "correlation"
    SENSITIVITY = "sensitivity"


@dataclass
class RiskLimit:
    """Represents a risk limit."""
    
    metric: RiskMetricType
    currency: Optional[str]  # None for all currencies
    limit_value: Decimal
    warning_threshold: Decimal  # Percentage of limit that triggers warning
    description: str
    is_active: bool = True


@dataclass
class RiskMetric:
    """Represents a calculated risk metric."""
    
    name: str
    value: Decimal
    timestamp: datetime.datetime
    confidence_level: Optional[float] = None
    time_horizon: Optional[int] = None  # In days
    currency: Optional[str] = None


class ForexRiskManager:
    """
    Foreign exchange risk manager.
    
    This class provides functionality for assessing and managing
    foreign exchange risk exposure.
    """
    
    def __init__(self, base_currency: str = "USD"):
        """
        Initialize the forex risk manager.
        
        Args:
            base_currency: Base currency for risk calculations
        """
        self.base_currency = base_currency
        self.risk_limits: List[RiskLimit] = []
        self.historical_rates: Dict[str, Dict[datetime.date, Dict[str, float]]] = {}
        self.current_positions: Dict[str, Decimal] = {}
        self.volatility_data: Dict[str, float] = {}
        self.correlation_matrix: Optional[pd.DataFrame] = None
    
    def set_risk_limit(self, metric: RiskMetricType,
                      limit_value: Decimal,
                      warning_threshold: Decimal,
                      description: str,
                      currency: Optional[str] = None) -> None:
        """
        Set a risk limit.
        
        Args:
            metric: Type of risk metric
            limit_value: Maximum allowed value
            warning_threshold: Warning threshold as percentage of limit
            description: Description of the limit
            currency: Specific currency or None for all currencies
        """
        # Remove any existing limit for this metric and currency
        self.risk_limits = [
            limit for limit in self.risk_limits
            if not (limit.metric == metric and limit.currency == currency)
        ]
        
        # Add new limit
        limit = RiskLimit(
            metric=metric,
            currency=currency,
            limit_value=limit_value,
            warning_threshold=warning_threshold,
            description=description
        )
        
        self.risk_limits.append(limit)
        logger.info(f"Set {metric.value} limit for {currency or 'all currencies'}: {limit_value}")
    
    def update_position(self, currency: str, position: Decimal) -> None:
        """
        Update currency position.
        
        Args:
            currency: Currency code
            position: Position amount
        """
        self.current_positions[currency] = position
    
    def add_historical_rates(self, base_currency: str,
                           quote_currency: str,
                           rates_data: Dict[datetime.date, float]) -> None:
        """
        Add historical exchange rate data.
        
        Args:
            base_currency: Base currency code
            quote_currency: Quote currency code
            rates_data: Dictionary mapping dates to rates
        """
        # Initialize dictionaries if needed
        if base_currency not in self.historical_rates:
            self.historical_rates[base_currency] = {}
            
        # Add rates for each date
        for date, rate in rates_data.items():
            if date not in self.historical_rates[base_currency]:
                self.historical_rates[base_currency][date] = {}
                
            self.historical_rates[base_currency][date][quote_currency] = rate
            
        logger.info(f"Added {len(rates_data)} historical rates for {base_currency}/{quote_currency}")
    
    def calculate_volatility(self, currency_pair: Tuple[str, str],
                           days: int = 30,
                           annualized: bool = True) -> float:
        """
        Calculate historical volatility for a currency pair.
        
        Args:
            currency_pair: Tuple of (base, quote) currencies
            days: Number of days to include
            annualized: Whether to annualize the volatility
            
        Returns:
            Volatility as decimal (e.g., 0.10 for 10%)
        """
        base, quote = currency_pair
        
        # Check if we have historical data
        if base not in self.historical_rates:
            logger.warning(f"No historical data for {base}")
            return 0.0
            
        # Get dates in descending order
        dates = sorted([d for d in self.historical_rates[base].keys() 
                      if quote in self.historical_rates[base][d]], reverse=True)
        
        if len(dates) < 2:
            logger.warning(f"Insufficient data for {base}/{quote}")
            return 0.0
            
        # Use at most the requested number of days
        dates = dates[:days]
        
        # Get rates
        rates = [self.historical_rates[base][date][quote] for date in dates]
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(rates)):
            returns.append(math.log(rates[i-1] / rates[i]))
            
        # Calculate standard deviation
        if not returns:
            return 0.0
            
        std_dev = np.std(returns, ddof=1)
        
        # Annualize if requested
        if annualized:
            std_dev *= math.sqrt(252)  # Approximately 252 trading days in a year
            
        # Store volatility
        pair_key = f"{base}/{quote}"
        self.volatility_data[pair_key] = std_dev
        
        return std_dev
        
    def calculate_correlation_matrix(self, currencies: List[str],
                                  days: int = 30) -> pd.DataFrame:
        """
        Calculate correlation matrix between currencies.
        
        Args:
            currencies: List of currency codes
            days: Number of days to include
            
        Returns:
            Pandas DataFrame with correlation matrix
        """
        # Prepare data for correlation calculation
        returns_data = {}
        
        for base in currencies:
            if base not in self.historical_rates:
                continue
                
            for quote in currencies:
                if base == quote:
                    continue
                    
                # Get dates where this pair has data
                dates = sorted([d for d in self.historical_rates[base].keys() 
                              if quote in self.historical_rates[base][d]], reverse=True)
                
                if len(dates) < 2:
                    continue
                    
                # Use at most the requested number of days
                dates = dates[:days]
                
                # Get rates and calculate returns
                rates = [self.historical_rates[base][date][quote] for date in dates]
                returns = []
                
                for i in range(1, len(rates)):
                    returns.append(math.log(rates[i-1] / rates[i]))
                    
                if returns:
                    pair_key = f"{base}/{quote}"
                    returns_data[pair_key] = returns
        
        # Create DataFrame from returns
        df = pd.DataFrame(returns_data)
        
        # Calculate correlation matrix
        if not df.empty:
            correlation = df.corr()
            self.correlation_matrix = correlation
            return correlation
        else:
            logger.warning("Insufficient data for correlation calculation")
            return pd.DataFrame()
    
    def calculate_var(self, currency: str,
                    position_amount: Optional[Decimal] = None,
                    confidence_level: float = 0.99,
                    days: int = 10,
                    method: str = 'historical') -> RiskMetric:
        """
        Calculate Value at Risk (VaR) for a currency position.
        
        Args:
            currency: Currency code
            position_amount: Position amount (uses current position if None)
            confidence_level: Confidence level (e.g., 0.95, 0.99)
            days: Time horizon in days
            method: VaR method ('historical', 'parametric', or 'monte_carlo')
            
        Returns:
            RiskMetric with calculated VaR
        """
        # Get position amount
        if position_amount is None:
            if currency not in self.current_positions:
                logger.warning(f"No position available for {currency}")
                return RiskMetric(
                    name=f"VaR_{currency}",
                    value=Decimal('0'),
                    timestamp=datetime.datetime.now(),
                    confidence_level=confidence_level,
                    time_horizon=days,
                    currency=currency
                )
            position_amount = self.current_positions[currency]
            
        # Get absolute position value (VaR is always positive)
        position_value = abs(float(position_amount))
        
        # Calculate VaR based on selected method
        if method == 'parametric':
            var = self._calculate_parametric_var(currency, position_value, confidence_level, days)
        elif method == 'monte_carlo':
            var = self._calculate_monte_carlo_var(currency, position_value, confidence_level, days)
        else:  # historical
            var = self._calculate_historical_var(currency, position_value, confidence_level, days)
            
        return RiskMetric(
            name=f"VaR_{currency}",
            value=Decimal(str(var)),
            timestamp=datetime.datetime.now(),
            confidence_level=confidence_level,
            time_horizon=days,
            currency=currency
        )
    
    def _calculate_historical_var(self, currency: str,
                               position_value: float,
                               confidence_level: float,
                               days: int) -> float:
        """Calculate VaR using historical simulation method."""
        # Use historical rates against base currency
        base = self.base_currency
        
        if base not in self.historical_rates:
            logger.warning(f"No historical data for {base}")
            return 0.0
        
        # Get dates where we have the currency rate
        dates = sorted([d for d in self.historical_rates[base].keys() 
                      if currency in self.historical_rates[base][d]], reverse=True)
        
        if len(dates) < 2:
            logger.warning(f"Insufficient data for {base}/{currency}")
            return 0.0
        
        # Get rates and calculate returns
        rates = [self.historical_rates[base][date][currency] for date in dates]
        returns = []
        
        for i in range(1, len(rates)):
            returns.append(rates[i-1] / rates[i] - 1)  # Simple return
        
        if not returns:
            return 0.0
        
        # Calculate VaR
        returns.sort()
        index = int(len(returns) * (1 - confidence_level))
        var_return = abs(returns[index])
        
        # Scale for time horizon
        var_return *= math.sqrt(days)
        
        # Calculate VaR in base currency
        var = position_value * var_return
        
        return var
    
    def _calculate_parametric_var(self, currency: str,
                               position_value: float,
                               confidence_level: float,
                               days: int) -> float:
        """Calculate VaR using parametric (variance-covariance) method."""
        # Get volatility
        pair = (self.base_currency, currency)
        volatility = self.calculate_volatility(pair, days=30, annualized=True)
        
        # Get z-score for confidence level
        z_score = stats.norm.ppf(confidence_level)
        
        # Calculate daily VaR
        daily_var = position_value * volatility * z_score / math.sqrt(252)
        
        # Scale for time horizon
        var = daily_var * math.sqrt(days)
        
        return var
    
    def _calculate_monte_carlo_var(self, currency: str,
                                position_value: float,
                                confidence_level: float,
                                days: int) -> float:
        """Calculate VaR using Monte Carlo simulation method."""
        # Get volatility
        pair = (self.base_currency, currency)
        volatility = self.calculate_volatility(pair, days=30, annualized=True)
        
        # Run simulation
        simulations = 10000
        daily_vol = volatility / math.sqrt(252)
        
        np.random.seed(42)  # for reproducibility
        z = np.random.normal(0, 1, simulations)
        simulated_returns = np.exp(z * daily_vol * math.sqrt(days) - 0.5 * daily_vol**2 * days) - 1
        
        # Calculate VaR
        simulated_returns.sort()
        index = int(simulations * (1 - confidence_level))
        var_return = abs(simulated_returns[index])
        
        # Calculate VaR in base currency
        var = position_value * var_return
        
        return var
    
    def calculate_expected_shortfall(self, currency: str,
                                  position_amount: Optional[Decimal] = None,
                                  confidence_level: float = 0.99,
                                  days: int = 10) -> RiskMetric:
        """
        Calculate Expected Shortfall (ES) for a currency position.
        
        Args:
            currency: Currency code
            position_amount: Position amount (uses current position if None)
            confidence_level: Confidence level
            days: Time horizon in days
            
        Returns:
            RiskMetric with calculated ES
        """
        # Get position amount
        if position_amount is None:
            if currency not in self.current_positions:
                logger.warning(f"No position available for {currency}")
                return RiskMetric(
                    name=f"ES_{currency}",
                    value=Decimal('0'),
                    timestamp=datetime.datetime.now(),
                    confidence_level=confidence_level,
                    time_horizon=days,
                    currency=currency
                )
            position_amount = self.current_positions[currency]
            
        # Get absolute position value
        position_value = abs(float(position_amount))
        
        # Use historical rates against base currency
        base = self.base_currency
        
        if base not in self.historical_rates:
            logger.warning(f"No historical data for {base}")
            return RiskMetric(
                name=f"ES_{currency}",
                value=Decimal('0'),
                timestamp=datetime.datetime.now(),
                confidence_level=confidence_level,
                time_horizon=days,
                currency=currency
            )
        
        # Get dates where we have the currency rate
        dates = sorted([d for d in self.historical_rates[base].keys() 
                      if currency in self.historical_rates[base][d]], reverse=True)
        
        if len(dates) < 2:
            logger.warning(f"Insufficient data for {base}/{currency}")
            return RiskMetric(
                name=f"ES_{currency}",
                value=Decimal('0'),
                timestamp=datetime.datetime.now(),
                confidence_level=confidence_level,
                time_horizon=days,
                currency=currency
            )
        
        # Get rates and calculate returns
        rates = [self.historical_rates[base][date][currency] for date in dates]
        returns = []
        
        for i in range(1, len(rates)):
            returns.append(rates[i-1] / rates[i] - 1)  # Simple return
        
        if not returns:
            return RiskMetric(
                name=f"ES_{currency}",
                value=Decimal('0'),
                timestamp=datetime.datetime.now(),
                confidence_level=confidence_level,
                time_horizon=days,
                currency=currency
            )
        
        # Calculate ES
        returns.sort()
        var_index = int(len(returns) * (1 - confidence_level))
        es_returns = returns[:var_index]
        es_return = abs(sum(es_returns) / len(es_returns))
        
        # Scale for time horizon
        es_return *= math.sqrt(days)
        
        # Calculate ES in base currency
        es = position_value * es_return
        
        return RiskMetric(
            name=f"ES_{currency}",
            value=Decimal(str(es)),
            timestamp=datetime.datetime.now(),
            confidence_level=confidence_level,
            time_horizon=days,
            currency=currency
        )
    
    def calculate_portfolio_var(self, 
                              confidence_level: float = 0.99,
                              days: int = 10) -> RiskMetric:
        """
        Calculate Value at Risk for the entire currency portfolio.
        
        Args:
            confidence_level: Confidence level
            days: Time horizon in days
            
        Returns:
            RiskMetric with calculated portfolio VaR
        """
        # Check if we have positions
        if not self.current_positions:
            logger.warning("No positions available for VaR calculation")
            return RiskMetric(
                name="Portfolio_VaR",
                value=Decimal('0'),
                timestamp=datetime.datetime.now(),
                confidence_level=confidence_level,
                time_horizon=days
            )
        
        # Check if we need to calculate correlation matrix
        currencies = list(self.current_positions.keys())
        if self.correlation_matrix is None or not all(curr in self.correlation_matrix for curr in currencies):
            self.calculate_correlation_matrix(currencies)
        
        # Calculate individual VaRs
        individual_vars = {}
        for currency, position in self.current_positions.items():
            var_metric = self.calculate_var(
                currency=currency,
                position_amount=position,
                confidence_level=confidence_level,
                days=days
            )
            individual_vars[currency] = float(var_metric.value)
        
        # Simple sum (ignoring correlation)
        sum_var = sum(individual_vars.values())
        
        # Use correlation if available
        if self.correlation_matrix is not None and not self.correlation_matrix.empty:
            # Create arrays for calculation
            var_array = []
            correlation_matrix = []
            
            # Check which currencies we have in the correlation matrix
            available_currencies = [c for c in currencies if c in self.correlation_matrix]
            
            if available_currencies:
                # Extract relevant parts of correlation matrix
                correlation_matrix = self.correlation_matrix.loc[available_currencies, available_currencies].values
                var_array = np.array([individual_vars.get(c, 0) for c in available_currencies])
                
                # Calculate diversified VaR
                diversified_var = math.sqrt(var_array.T @ correlation_matrix @ var_array)
                
                # If successful, use the diversified value
                if not np.isnan(diversified_var) and diversified_var > 0:
                    sum_var = diversified_var
        
        return RiskMetric(
            name="Portfolio_VaR",
            value=Decimal(str(sum_var)),
            timestamp=datetime.datetime.now(),
            confidence_level=confidence_level,
            time_horizon=days
        )
    
    def calculate_sensitivity(self, currency: str, 
                           position_amount: Optional[Decimal] = None,
                           move_percent: float = 0.01) -> RiskMetric:
        """
        Calculate sensitivity to exchange rate movements.
        
        Args:
            currency: Currency code
            position_amount: Position amount (uses current position if None)
            move_percent: Percentage move to calculate sensitivity for
            
        Returns:
            RiskMetric with calculated sensitivity
        """
        # Get position amount
        if position_amount is None:
            if currency not in self.current_positions:
                logger.warning(f"No position available for {currency}")
                return RiskMetric(
                    name=f"Sensitivity_{currency}",
                    value=Decimal('0'),
                    timestamp=datetime.datetime.now(),
                    currency=currency
                )
            position_amount = self.current_positions[currency]
            
        # Calculate sensitivity (simple linear approach)
        sensitivity = float(abs(position_amount)) * move_percent
        
        return RiskMetric(
            name=f"Sensitivity_{currency}",
            value=Decimal(str(sensitivity)),
            timestamp=datetime.datetime.now(),
            currency=currency
        )
    
    def check_risk_limits(self) -> List[Dict[str, Any]]:
        """
        Check if any risk metrics exceed defined limits.
        
        Returns:
            List of breaches with details
        """
        breaches = []
        
        for limit in self.risk_limits:
            if not limit.is_active:
                continue
                
            # Get currencies to check
            currencies = [limit.currency] if limit.currency else list(self.current_positions.keys())
            
            for currency in currencies:
                metric_value = None
                
                # Calculate appropriate metric
                if limit.metric == RiskMetricType.VAR:
                    metric = self.calculate_var(currency)
                    metric_value = float(metric.value)
                    
                elif limit.metric == RiskMetricType.EXPECTED_SHORTFALL:
                    metric = self.calculate_expected_shortfall(currency)
                    metric_value = float(metric.value)
                    
                elif limit.metric == RiskMetricType.VOLATILITY:
                    if self.base_currency != currency:
                        vol = self.calculate_volatility((self.base_currency, currency))
                        metric_value = vol
                        
                elif limit.metric == RiskMetricType.SENSITIVITY:
                    metric = self.calculate_sensitivity(currency)
                    metric_value = float(metric.value)
                
                # Skip if we couldn't calculate the metric
                if metric_value is None:
                    continue
                    
                # Check for limit breach
                limit_value = float(limit.limit_value)
                warning_threshold = float(limit.warning_threshold)
                
                if metric_value > limit_value:
                    breaches.append({
                        "currency": currency,
                        "metric": limit.metric.value,
                        "value": metric_value,
                        "limit": limit_value,
                        "excess": metric_value - limit_value,
                        "excess_percentage": (metric_value / limit_value - 1) * 100,
                        "severity": "breach"
                    })
                    logger.warning(f"LIMIT BREACH: {limit.metric.value} for {currency} "
                                   f"exceeded by {metric_value - limit_value:.2f}")
                    
                elif metric_value > limit_value * warning_threshold:
                    breaches.append({
                        "currency": currency,
                        "metric": limit.metric.value,
                        "value": metric_value,
                        "limit": limit_value,
                        "warning_threshold": limit_value * warning_threshold,
                        "severity": "warning"
                    })
                    logger.info(f"LIMIT WARNING: {limit.metric.value} for {currency} "
                               f"approaching limit ({metric_value:.2f} vs {limit_value:.2f})")
        
        return breaches
    
    def run_stress_test(self, scenarios: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Run stress tests based on defined scenarios.
        
        Args:
            scenarios: Dictionary of scenario name to currency moves
                       {'severe_usd_rise': {'EUR': -0.10, 'GBP': -0.08, ...}, ...}
            
        Returns:
            Dictionary mapping scenario names to PnL impact
        """
        results = {}
        
        for scenario_name, currency_moves in scenarios.items():
            # Calculate PnL impact for this scenario
            total_pnl = 0
            
            for currency, position in self.current_positions.items():
                # Skip if no move defined for this currency or position is zero
                if currency not in currency_moves or position == 0:
                    continue
                    
                # Get position in base currency
                move_percent = currency_moves[currency]
                
                # Calculate PnL impact (positive move = profit for long position)
                pnl_impact = float(position) * move_percent
                total_pnl += pnl_impact
            
            results[scenario_name] = total_pnl
            logger.info(f"Stress test - {scenario_name}: PnL impact = {total_pnl:.2f}")
        
        return results
    
    def plot_risk_metrics(self, currency: str = None, 
                        days: int = 30,
                        output_path: Optional[str] = None) -> Optional[str]:
        """
        Plot risk metrics for a currency or the whole portfolio.
        
        Args:
            currency: Specific currency or None for portfolio
            days: Number of days to include
            output_path: Path to save the plot (optional)
            
        Returns:
            Path to saved plot or None if displayed
        """
        plt.figure(figsize=(12, 8))
        
        # Define confidence levels to plot
        confidence_levels = [0.95, 0.99]
        
        # Create x-axis values for time horizons
        horizons = list(range(1, days + 1))
        
        # Plot VaR for each confidence level
        for cl in confidence_levels:
            var_values = []
            
            for horizon in horizons:
                if currency:
                    # Single currency VaR
                    metric = self.calculate_var(currency, confidence_level=cl, days=horizon)
                    var_values.append(float(metric.value))
                else:
                    # Portfolio VaR
                    metric = self.calculate_portfolio_var(confidence_level=cl, days=horizon)
                    var_values.append(float(metric.value))
            
            plt.plot(horizons, var_values, label=f"VaR ({cl:.0%})")
            
        # Add labels and legend
        title = f"Value at Risk - {currency}" if currency else "Portfolio Value at Risk"
        plt.title(title)
        plt.xlabel("Time Horizon (Days)")
        plt.ylabel(f"VaR ({self.base_currency})")
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Save or display
        if output_path:
            plt.savefig(output_path)
            plt.close()
            return output_path
        else:
            plt.show()
            plt.close()
            return None

# Example usage
if __name__ == "__main__":
    # Create forex risk manager
    risk_manager = ForexRiskManager("USD")
    
    # Set current positions
    risk_manager.update_position("EUR", Decimal("1000000"))
    risk_manager.update_position("GBP", Decimal("500000"))
    risk_manager.update_position("JPY", Decimal("50000000"))
    
    # Add historical data (simplified example)
    today = datetime.date.today()
    historical_data_eur = {}
    historical_data_gbp = {}
    
    # Generate sample historical data
    np.random.seed(42)
    for i in range(100):
        date = today - datetime.timedelta(days=i)
        # Simulate rates with some randomness
        historical_data_eur[date] = 1.10 + np.random.normal(0, 0.01)
        historical_data_gbp[date] = 1.30 + np.random.normal(0, 0.015)
    
    risk_manager.add_historical_rates("USD", "EUR", historical_data_eur)
    risk_manager.add_historical_rates("USD", "GBP", historical_data_gbp)
    
    # Calculate volatility
    eur_vol = risk_manager.calculate_volatility(("USD", "EUR"))
    gbp_vol = risk_manager.calculate_volatility(("USD", "GBP"))
    print(f"EUR/USD Volatility: {eur_vol:.2%}")
    print(f"GBP/USD Volatility: {gbp_vol:.2%}")
    
    # Calculate VaR
    eur_var = risk_manager.calculate_var("EUR")
    print(f"EUR VaR (99%, 10-day): {float(eur_var.value):.2f}")
    
    portfolio_var = risk_manager.calculate_portfolio_var()
    print(f"Portfolio VaR (99%, 10-day): {float(portfolio_var.value):.2f}")
    
    # Set risk limits
    risk_manager.set_risk_limit(
        RiskMetricType.VAR,
        Decimal("50000"),
        Decimal("0.8"),
        "Maximum VaR for EUR positions",
        "EUR"
    )
    
    # Check limits
    breaches = risk_manager.check_risk_limits()
    for breach in breaches:
        print(f"BREACH: {breach['metric']} for {breach['currency']}: " +
              f"{breach['value']:.2f} vs. limit {breach['limit']:.2f}")
    
    # Run stress test
    scenarios = {
        "eur_drop": {"EUR": -0.05, "GBP": -0.02},
        "usd_strengthen": {"EUR": -0.08, "GBP": -0.06, "JPY": -0.10}
    }
    
    stress_results = risk_manager.run_stress_test(scenarios)
    for scenario, impact in stress_results.items():
        print(f"Stress test - {scenario}: {impact:.2f}")
