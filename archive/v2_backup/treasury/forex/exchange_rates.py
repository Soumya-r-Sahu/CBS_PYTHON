"""
Exchange Rates module for treasury operations.

This module provides functionality for tracking, retrieving, forecasting
and analyzing exchange rates between currency pairs.
"""

import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
import logging
import json
import requests
import pandas as pd
import numpy as np
from pathlib import Path
import csv
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ExchangeRate:
    """Represents an exchange rate between two currencies at a point in time."""
    
    base_currency: str           # From currency (e.g., USD)
    quote_currency: str          # To currency (e.g., EUR)
    rate: Decimal                # Exchange rate (1 base = rate quote)
    timestamp: datetime.datetime # When the rate was recorded/retrieved
    bid: Optional[Decimal] = None  # Bid price if available
    ask: Optional[Decimal] = None  # Ask price if available
    source: Optional[str] = None   # Data source
    
    @property
    def inverse_rate(self) -> Decimal:
        """Calculate inverse exchange rate (quote to base)."""
        if self.rate == 0:
            return Decimal('0')
        return Decimal('1') / self.rate
    
    @property
    def spread(self) -> Optional[Decimal]:
        """Calculate spread if bid and ask are available."""
        if self.bid is not None and self.ask is not None and self.bid > 0:
            return (self.ask - self.bid) / self.bid
        return None


class ExchangeRateManager:
    """
    Manages exchange rate data for various currency pairs.
    
    This class provides functionality to retrieve, store, analyze, and
    forecast exchange rates.
    """
    
    def __init__(self, base_currency: str = "USD"):
        """
        Initialize the exchange rate manager.
        
        Args:
            base_currency: Default base currency
        """
        self.base_currency = base_currency
        self.current_rates: Dict[str, Dict[str, ExchangeRate]] = {}
        self.historical_rates: Dict[datetime.date, Dict[str, Dict[str, Decimal]]] = {}
        self.api_keys: Dict[str, str] = {}
        self._data_directory = None
        
    def set_data_directory(self, directory_path: str) -> None:
        """
        Set directory for storing rate data files.
        
        Args:
            directory_path: Path to data directory
        """
        path = Path(directory_path)
        path.mkdir(exist_ok=True, parents=True)
        self._data_directory = path
        logger.info(f"Set exchange rate data directory: {directory_path}")
    
    def add_api_key(self, provider: str, api_key: str) -> None:
        """
        Add API key for a data provider.
        
        Args:
            provider: Provider name
            api_key: API key
        """
        self.api_keys[provider] = api_key
        logger.info(f"Added API key for {provider}")
    
    def fetch_rates_from_api(self, 
                           provider: str, 
                           currency_pairs: Optional[List[Tuple[str, str]]] = None) -> bool:
        """
        Fetch exchange rates from an external API.
        
        Args:
            provider: API provider name
            currency_pairs: List of (base, quote) currency pairs to fetch
            
        Returns:
            True if successful, False otherwise
        """
        if provider not in self.api_keys:
            logger.error(f"No API key available for provider: {provider}")
            return False
            
        api_key = self.api_keys[provider]
        base_currency = self.base_currency
        
        # If no pairs specified, use default base currency with common quotes
        if not currency_pairs:
            currency_pairs = [
                (base_currency, "EUR"),
                (base_currency, "GBP"),
                (base_currency, "JPY"),
                (base_currency, "CHF"),
                (base_currency, "CAD"),
                (base_currency, "AUD"),
                (base_currency, "CNY")
            ]
        
        timestamp = datetime.datetime.now()
        
        # Example implementation for different providers
        try:
            if provider.lower() == "exchangerate-api":
                # Example for exchangerate-api.com
                for base, quote in currency_pairs:
                    url = f"https://api.exchangerate-api.com/v4/latest/{base}"
                    response = requests.get(url, params={"api_key": api_key})
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "rates" in data and quote in data["rates"]:
                            rate = Decimal(str(data["rates"][quote]))
                            self._add_rate(base, quote, rate, timestamp, source=provider)
                        else:
                            logger.warning(f"No rate found for {base}/{quote}")
                    else:
                        logger.error(f"API error: {response.status_code} - {response.text}")
                
            elif provider.lower() == "fixer":
                # Example for fixer.io
                symbols = ",".join([pair[1] for pair in currency_pairs])
                bases = set([pair[0] for pair in currency_pairs])
                
                for base in bases:
                    url = "http://data.fixer.io/api/latest"
                    params = {
                        "access_key": api_key,
                        "base": base,
                        "symbols": symbols
                    }
                    
                    response = requests.get(url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success") and "rates" in data:
                            for quote, rate_value in data["rates"].items():
                                rate = Decimal(str(rate_value))
                                self._add_rate(base, quote, rate, timestamp, source=provider)
                    else:
                        logger.error(f"API error: {response.status_code} - {response.text}")
                        
            else:
                logger.error(f"Unsupported provider: {provider}")
                return False
                
            logger.info(f"Updated exchange rates from {provider}")
            return True
            
        except Exception as e:
            logger.error(f"Error fetching rates from {provider}: {str(e)}")
            return False
    
    def _add_rate(self, 
                 base_currency: str, 
                 quote_currency: str, 
                 rate: Decimal, 
                 timestamp: datetime.datetime, 
                 bid: Optional[Decimal] = None,
                 ask: Optional[Decimal] = None,
                 source: Optional[str] = None) -> None:
        """
        Add an exchange rate to the current rates.
        
        Args:
            base_currency: Base currency code
            quote_currency: Quote currency code
            rate: Exchange rate
            timestamp: Rate timestamp
            bid: Bid price (optional)
            ask: Ask price (optional)
            source: Data source (optional)
        """
        # Initialize dictionaries if needed
        if base_currency not in self.current_rates:
            self.current_rates[base_currency] = {}
        
        # Create exchange rate object
        exchange_rate = ExchangeRate(
            base_currency=base_currency,
            quote_currency=quote_currency,
            rate=rate,
            timestamp=timestamp,
            bid=bid,
            ask=ask,
            source=source
        )
        
        # Store the rate
        self.current_rates[base_currency][quote_currency] = exchange_rate
        
        # Add to historical data (daily resolution)
        date = timestamp.date()
        if date not in self.historical_rates:
            self.historical_rates[date] = {}
        
        if base_currency not in self.historical_rates[date]:
            self.historical_rates[date][base_currency] = {}
            
        self.historical_rates[date][base_currency][quote_currency] = rate
    
    def get_rate(self, 
               base_currency: str, 
               quote_currency: str) -> Optional[ExchangeRate]:
        """
        Get the current exchange rate for a currency pair.
        
        Args:
            base_currency: Base currency code
            quote_currency: Quote currency code
            
        Returns:
            Exchange rate or None if not available
        """
        # Direct lookup
        if base_currency in self.current_rates and quote_currency in self.current_rates[base_currency]:
            return self.current_rates[base_currency][quote_currency]
        
        # Try inverse rate
        if quote_currency in self.current_rates and base_currency in self.current_rates[quote_currency]:
            inverse = self.current_rates[quote_currency][base_currency]
            return ExchangeRate(
                base_currency=base_currency,
                quote_currency=quote_currency,
                rate=inverse.inverse_rate,
                timestamp=inverse.timestamp,
                source=inverse.source
            )
        
        # Try triangulation via common currency (e.g., USD)
        common_currencies = [self.base_currency]
        for common in common_currencies:
            if (common != base_currency and common != quote_currency and
                base_currency in self.current_rates and common in self.current_rates[base_currency] and
                common in self.current_rates and quote_currency in self.current_rates[common]):
                
                rate1 = self.current_rates[base_currency][common]
                rate2 = self.current_rates[common][quote_currency]
                
                # Calculate triangulated rate
                triangulated_rate = rate1.rate * rate2.rate
                
                # Use most recent timestamp
                timestamp = max(rate1.timestamp, rate2.timestamp)
                
                return ExchangeRate(
                    base_currency=base_currency,
                    quote_currency=quote_currency,
                    rate=triangulated_rate,
                    timestamp=timestamp,
                    source=f"Triangulated via {common}"
                )
        
        return None
    
    def convert_amount(self, 
                     amount: Decimal, 
                     from_currency: str, 
                     to_currency: str) -> Optional[Decimal]:
        """
        Convert an amount between currencies.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Converted amount or None if conversion not possible
        """
        if from_currency == to_currency:
            return amount
            
        rate = self.get_rate(from_currency, to_currency)
        if rate:
            return amount * rate.rate
        
        logger.warning(f"No exchange rate available for {from_currency}/{to_currency}")
        return None
    
    def save_rates_to_csv(self, file_path: Optional[str] = None) -> Optional[str]:
        """
        Save current rates to a CSV file.
        
        Args:
            file_path: Path to output file (optional)
            
        Returns:
            Path to the saved file or None if save failed
        """
        if not file_path and not self._data_directory:
            logger.error("No file path or data directory specified")
            return None
            
        if not file_path:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = self._data_directory / f"exchange_rates_{timestamp}.csv"
        
        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                writer.writerow(['Base', 'Quote', 'Rate', 'Timestamp', 'Source'])
                
                # Write data
                for base, quotes in self.current_rates.items():
                    for quote, rate_obj in quotes.items():
                        writer.writerow([
                            base,
                            quote,
                            float(rate_obj.rate),
                            rate_obj.timestamp.isoformat(),
                            rate_obj.source or 'Unknown'
                        ])
                        
            logger.info(f"Saved exchange rates to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving exchange rates to CSV: {str(e)}")
            return None
    
    def load_rates_from_csv(self, file_path: str) -> bool:
        """
        Load exchange rates from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    base = row['Base']
                    quote = row['Quote']
                    rate = Decimal(str(row['Rate']))
                    timestamp = datetime.datetime.fromisoformat(row['Timestamp'])
                    source = row.get('Source', 'CSV Import')
                    
                    self._add_rate(base, quote, rate, timestamp, source=source)
                    
            logger.info(f"Loaded exchange rates from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading exchange rates from CSV: {str(e)}")
            return False
    
    def get_historical_series(self, 
                            base_currency: str, 
                            quote_currency: str,
                            days: int = 30) -> Dict[datetime.date, Decimal]:
        """
        Get historical exchange rate series for a currency pair.
        
        Args:
            base_currency: Base currency code
            quote_currency: Quote currency code
            days: Number of days to retrieve
            
        Returns:
            Dictionary mapping dates to rates
        """
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=days)
        
        result = {}
        for date in sorted(self.historical_rates.keys()):
            if start_date <= date <= today:
                if (base_currency in self.historical_rates[date] and 
                    quote_currency in self.historical_rates[date][base_currency]):
                    result[date] = self.historical_rates[date][base_currency][quote_currency]
                    
        return result
    
    def forecast_rate(self, 
                    base_currency: str, 
                    quote_currency: str,
                    days_ahead: int = 5,
                    history_days: int = 60) -> List[Tuple[datetime.date, float]]:
        """
        Forecast exchange rate using ARIMA model.
        
        Args:
            base_currency: Base currency code
            quote_currency: Quote currency code
            days_ahead: Number of days to forecast
            history_days: Number of historical days to use
            
        Returns:
            List of (date, rate) tuples for the forecasted period
        """
        # Get historical data
        historical_data = self.get_historical_series(base_currency, quote_currency, history_days)
        
        if len(historical_data) < 10:
            logger.warning(f"Insufficient data for forecasting {base_currency}/{quote_currency}")
            return []
            
        try:
            # Convert to pandas series
            dates = list(historical_data.keys())
            rates = [float(historical_data[d]) for d in dates]
            
            series = pd.Series(rates, index=dates)
            
            # Fit ARIMA model
            model = ARIMA(series, order=(2, 1, 2))
            model_fit = model.fit()
            
            # Forecast future values
            forecast = model_fit.forecast(steps=days_ahead)
            
            # Generate future dates
            last_date = max(dates)
            future_dates = [last_date + datetime.timedelta(days=i+1) for i in range(days_ahead)]
            
            # Combine dates with forecasted values
            return list(zip(future_dates, forecast))
            
        except Exception as e:
            logger.error(f"Error forecasting rates: {str(e)}")
            return []
    
    def plot_rate_history(self, 
                        base_currency: str, 
                        quote_currency: str,
                        days: int = 30,
                        show_forecast: bool = True,
                        output_path: Optional[str] = None) -> Optional[str]:
        """
        Plot historical and optionally forecasted rates.
        
        Args:
            base_currency: Base currency code
            quote_currency: Quote currency code
            days: Number of days of history to plot
            show_forecast: Whether to include forecasted rates
            output_path: Path to save the plot (optional)
            
        Returns:
            Path to the saved plot or None if plot failed
        """
        # Get historical data
        historical_data = self.get_historical_series(base_currency, quote_currency, days)
        
        if not historical_data:
            logger.warning(f"No historical data available for {base_currency}/{quote_currency}")
            return None
            
        try:
            # Prepare plot data
            dates = list(historical_data.keys())
            rates = [float(historical_data[d]) for d in dates]
            
            plt.figure(figsize=(10, 6))
            plt.plot(dates, rates, 'b-', label=f'Historical {base_currency}/{quote_currency}')
            
            # Add forecast if requested
            if show_forecast:
                forecast_days = min(5, days // 4)  # Forecast up to 5 days or 1/4 of history
                forecast_data = self.forecast_rate(
                    base_currency, quote_currency, forecast_days, days
                )
                
                if forecast_data:
                    forecast_dates, forecast_rates = zip(*forecast_data)
                    plt.plot(forecast_dates, forecast_rates, 'r--', label='Forecast')
                    
                    # Add confidence interval (simple approximation)
                    std_dev = np.std(rates)
                    upper = [r + 1.96 * std_dev for r in forecast_rates]
                    lower = [r - 1.96 * std_dev for r in forecast_rates]
                    plt.fill_between(forecast_dates, lower, upper, color='red', alpha=0.2)
            
            # Format plot
            plt.title(f'{base_currency}/{quote_currency} Exchange Rate')
            plt.xlabel('Date')
            plt.ylabel(f'Rate (1 {base_currency} to {quote_currency})')
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Save or show plot
            if output_path:
                plt.savefig(output_path)
                plt.close()
                logger.info(f"Saved exchange rate plot to {output_path}")
                return output_path
            else:
                plt.show()
                plt.close()
                return None
                
        except Exception as e:
            logger.error(f"Error plotting exchange rates: {str(e)}")
            return None

# Example usage
if __name__ == "__main__":
    # Create exchange rate manager
    manager = ExchangeRateManager("USD")
    
    # Set data directory
    manager.set_data_directory("./exchange_rate_data")
    
    # Add some sample rates
    now = datetime.datetime.now()
    
    # USD to other currencies
    manager._add_rate("USD", "EUR", Decimal("0.85"), now, source="Example")
    manager._add_rate("USD", "GBP", Decimal("0.75"), now, source="Example")
    manager._add_rate("USD", "JPY", Decimal("110.25"), now, source="Example")
    manager._add_rate("USD", "CAD", Decimal("1.25"), now, source="Example")
    
    # EUR to others
    manager._add_rate("EUR", "GBP", Decimal("0.88"), now, source="Example")
    
    # Get a rate
    eur_rate = manager.get_rate("USD", "EUR")
    if eur_rate:
        print(f"USD/EUR: {eur_rate.rate}")
    
    # Convert an amount
    amount_usd = Decimal("1000")
    amount_eur = manager.convert_amount(amount_usd, "USD", "EUR")
    if amount_eur:
        print(f"USD {amount_usd} = EUR {amount_eur}")
    
    # Try triangulation
    jpy_gbp = manager.get_rate("JPY", "GBP")
    if jpy_gbp:
        print(f"JPY/GBP (triangulated): {jpy_gbp.rate}")
