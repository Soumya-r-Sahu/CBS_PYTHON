"""
Liquidity Dashboard for treasury operations.

This module provides functionality for monitoring and visualizing liquidity metrics,
including cash positions, regulatory ratios, and liquidity projections.
"""

import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
import logging
import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class LiquiditySnapshot:
    """Represents a snapshot of the bank's liquidity position at a point in time."""
    
    date: datetime.date
    total_cash: Decimal
    high_quality_liquid_assets: Decimal
    short_term_obligations: Decimal
    stable_funding: Decimal
    required_stable_funding: Decimal
    currency_breakdown: Dict[str, Decimal] = field(default_factory=dict)
    intraday_min: Optional[Decimal] = None
    intraday_max: Optional[Decimal] = None
    
    @property
    def lcr(self) -> Decimal:
        """Calculate Liquidity Coverage Ratio."""
        if self.short_term_obligations <= 0:
            return Decimal('999.99')  # Avoid division by zero
        return (self.high_quality_liquid_assets / self.short_term_obligations).quantize(Decimal('0.01'))
    
    @property
    def nsfr(self) -> Decimal:
        """Calculate Net Stable Funding Ratio."""
        if self.required_stable_funding <= 0:
            return Decimal('999.99')  # Avoid division by zero
        return (self.stable_funding / self.required_stable_funding).quantize(Decimal('0.01'))


class LiquidityDashboard:
    """Dashboard for monitoring and visualizing liquidity metrics."""
    
    def __init__(self, bank_name: str):
        """
        Initialize a liquidity dashboard.
        
        Args:
            bank_name: Name of the bank for reporting purposes
        """
        self.bank_name = bank_name
        self.snapshots: Dict[datetime.date, LiquiditySnapshot] = {}
        self.lcr_threshold = Decimal('1.00')
        self.nsfr_threshold = Decimal('1.00')
        self.cash_reserve_target = Decimal('0.15')  # 15% of total assets
        self.total_assets = Decimal('0')
        
    def add_snapshot(self, snapshot: LiquiditySnapshot) -> None:
        """
        Add a liquidity snapshot to the dashboard.
        
        Args:
            snapshot: The liquidity snapshot to add
        """
        self.snapshots[snapshot.date] = snapshot
        logger.info(f"Added liquidity snapshot for {snapshot.date}")
        
    def get_latest_snapshot(self) -> Optional[LiquiditySnapshot]:
        """
        Get the most recent liquidity snapshot.
        
        Returns:
            The most recent liquidity snapshot, or None if no snapshots exist
        """
        if not self.snapshots:
            return None
            
        latest_date = max(self.snapshots.keys())
        return self.snapshots[latest_date]
        
    def get_historical_snapshots(self, 
                                days: int, 
                                end_date: Optional[datetime.date] = None) -> Dict[datetime.date, LiquiditySnapshot]:
        """
        Get historical liquidity snapshots for a specified number of days.
        
        Args:
            days: Number of days to retrieve
            end_date: End date (default: today)
            
        Returns:
            Dictionary mapping dates to liquidity snapshots
        """
        if not self.snapshots:
            return {}
            
        end = end_date or datetime.date.today()
        start = end - datetime.timedelta(days=days)
        
        return {date: snapshot for date, snapshot in self.snapshots.items() 
                if start <= date <= end}
    
    def get_liquidity_alerts(self) -> List[str]:
        """
        Get alerts for liquidity metrics that breach thresholds.
        
        Returns:
            List of alert messages
        """
        alerts = []
        latest = self.get_latest_snapshot()
        
        if not latest:
            return ["No liquidity data available"]
            
        # Check LCR
        if latest.lcr < self.lcr_threshold:
            alerts.append(f"LCR below threshold: {latest.lcr:.2f} (threshold: {self.lcr_threshold:.2f})")
            
        # Check NSFR
        if latest.nsfr < self.nsfr_threshold:
            alerts.append(f"NSFR below threshold: {latest.nsfr:.2f} (threshold: {self.nsfr_threshold:.2f})")
            
        # Check cash reserves
        if self.total_assets > 0:
            cash_ratio = latest.total_cash / self.total_assets
            if cash_ratio < self.cash_reserve_target:
                alerts.append(f"Cash reserves below target: {cash_ratio:.2%} (target: {self.cash_reserve_target:.2%})")
                
        return alerts
        
    def get_liquidity_summary(self) -> Dict[str, Any]:
        """
        Get a summary of key liquidity metrics.
        
        Returns:
            Dictionary containing key liquidity metrics
        """
        latest = self.get_latest_snapshot()
        
        if not latest:
            return {"status": "No data available"}
            
        # Calculate 30-day trend if available
        lcr_trend = self._calculate_metric_trend("lcr", 30)
        nsfr_trend = self._calculate_metric_trend("nsfr", 30)
        cash_trend = self._calculate_metric_trend("total_cash", 30)
        
        return {
            "date": latest.date.isoformat(),
            "total_cash": float(latest.total_cash),
            "high_quality_liquid_assets": float(latest.high_quality_liquid_assets),
            "lcr": float(latest.lcr),
            "lcr_threshold": float(self.lcr_threshold),
            "lcr_status": "OK" if latest.lcr >= self.lcr_threshold else "ALERT",
            "lcr_trend": lcr_trend,
            "nsfr": float(latest.nsfr),
            "nsfr_threshold": float(self.nsfr_threshold),
            "nsfr_status": "OK" if latest.nsfr >= self.nsfr_threshold else "ALERT",
            "nsfr_trend": nsfr_trend,
            "cash_trend": cash_trend,
            "currency_breakdown": {k: float(v) for k, v in latest.currency_breakdown.items()},
            "alerts": self.get_liquidity_alerts()
        }
        
    def _calculate_metric_trend(self, metric_name: str, days: int) -> str:
        """
        Calculate trend direction for a metric over specified days.
        
        Args:
            metric_name: Name of the metric attribute
            days: Number of days to analyze
            
        Returns:
            Trend direction: "up", "down", "flat", or "insufficient_data"
        """
        snapshots = self.get_historical_snapshots(days)
        
        if len(snapshots) < 2:
            return "insufficient_data"
            
        # Sort snapshots by date
        sorted_dates = sorted(snapshots.keys())
        
        # Get oldest and newest values
        oldest = getattr(snapshots[sorted_dates[0]], metric_name)
        newest = getattr(snapshots[sorted_dates[-1]], metric_name)
        
        # Calculate percentage change
        if isinstance(oldest, Decimal) and isinstance(newest, Decimal):
            if oldest == 0:
                return "up" if newest > 0 else "flat"
                
            change_pct = float((newest - oldest) / oldest * 100)
            
            if abs(change_pct) < 1.0:  # Less than 1% change is considered flat
                return "flat"
            elif change_pct > 0:
                return "up"
            else:
                return "down"
        else:
            return "insufficient_data"
            
    def generate_lcr_nsfr_chart(self,days: int = 90,output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate a chart of LCR and NSFR trends.
        
        Args:
            days: Number of days to include in the chart
            output_path: Path to save the chart (optional)
            
        Returns:
            Path to the saved chart file, or None if no data available
        """
        snapshots = self.get_historical_snapshots(days)
        
        if len(snapshots) < 2:
            logger.warning("Insufficient data for chart generation")
            return None
            
        # Prepare data
        dates = []
        lcr_values = []
        nsfr_values = []
        
        for date in sorted(snapshots.keys()):
            snapshot = snapshots[date]
            dates.append(date)
            lcr_values.append(float(snapshot.lcr))
            nsfr_values.append(float(snapshot.nsfr))
            
        # Create chart
        plt.figure(figsize=(10, 6))
        plt.plot(dates, lcr_values, 'b-', label='LCR')
        plt.plot(dates, nsfr_values, 'g-', label='NSFR')
        
        # Add threshold lines
        plt.axhline(y=float(self.lcr_threshold), color='b', linestyle='--', alpha=0.7)
        plt.axhline(y=float(self.nsfr_threshold), color='g', linestyle='--', alpha=0.7)
        
        # Formatting
        plt.title(f'{self.bank_name} - Liquidity Ratios Trend')
        plt.xlabel('Date')
        plt.ylabel('Ratio')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Save or show
        if output_path:
            plt.savefig(output_path)
            plt.close()
            return output_path
        else:
            plt.show()
            plt.close()
            return None
            
    def generate_cash_position_chart(self, days: int = 90,output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate a chart of cash position trend.
        
        Args:
            days: Number of days to include in the chart
            output_path: Path to save the chart (optional)
            
        Returns:
            Path to the saved chart file, or None if no data available
        """
        snapshots = self.get_historical_snapshots(days)
        
        if len(snapshots) < 2:
            logger.warning("Insufficient data for chart generation")
            return None
            
        # Prepare data
        dates = []
        cash_values = []
        hqla_values = []
        
        for date in sorted(snapshots.keys()):
            snapshot = snapshots[date]
            dates.append(date)
            cash_values.append(float(snapshot.total_cash))
            hqla_values.append(float(snapshot.high_quality_liquid_assets))
            
        # Create chart
        plt.figure(figsize=(10, 6))
        plt.plot(dates, cash_values, 'b-', label='Total Cash')
        plt.plot(dates, hqla_values, 'r-', label='HQLA')
        
        # Formatting
        plt.title(f'{self.bank_name} - Cash Position Trend')
        plt.xlabel('Date')
        plt.ylabel('Amount')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Format y-axis with appropriate scale
        plt.gca().get_yaxis().set_major_formatter(
            plt.matplotlib.ticker.FuncFormatter(lambda x, loc: f"${x/1000000:.1f}M" if x >= 1000000 
                                                else f"${x/1000:.1f}K"))
        
        # Save or show
        if output_path:
            plt.savefig(output_path)
            plt.close()
            return output_path
        else:
            plt.show()
            plt.close()
            return None
            
    def generate_currency_breakdown_chart(self,
                                        date: Optional[datetime.date] = None,
                                        output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate a pie chart of currency breakdown.
        
        Args:
            date: Date for the snapshot (default: latest)
            output_path: Path to save the chart (optional)
            
        Returns:
            Path to the saved chart file, or None if no data available
        """
        if date:
            if date not in self.snapshots:
                logger.warning(f"No data available for {date}")
                return None
            snapshot = self.snapshots[date]
        else:
            snapshot = self.get_latest_snapshot()
            
        if not snapshot or not snapshot.currency_breakdown:
            logger.warning("No currency breakdown data available")
            return None
            
        # Prepare data
        currencies = list(snapshot.currency_breakdown.keys())
        values = [float(snapshot.currency_breakdown[c]) for c in currencies]
        
        # Create chart
        plt.figure(figsize=(8, 8))
        plt.pie(values, labels=currencies, autopct='%1.1f%%')
        
        # Formatting
        plt.title(f'{self.bank_name} - Currency Breakdown ({snapshot.date.isoformat()})')
        
        # Save or show
        if output_path:
            plt.savefig(output_path)
            plt.close()
            return output_path
        else:
            plt.show()
            plt.close()
            return None
    
    def export_dashboard_data(self, output_path: str, format: str = 'json') -> str:
        """
        Export dashboard data to a file.
        
        Args:
            output_path: Path to save the exported data
            format: Export format ('json' or 'csv')
            
        Returns:
            Path to the exported file
        """
        if format.lower() == 'json':
            # Convert data to JSON compatible format
            data = {
                "bank_name": self.bank_name,
                "lcr_threshold": float(self.lcr_threshold),
                "nsfr_threshold": float(self.nsfr_threshold),
                "snapshots": {
                    date.isoformat(): {
                        "total_cash": float(s.total_cash),
                        "high_quality_liquid_assets": float(s.high_quality_liquid_assets),
                        "short_term_obligations": float(s.short_term_obligations),
                        "stable_funding": float(s.stable_funding),
                        "required_stable_funding": float(s.required_stable_funding),
                        "lcr": float(s.lcr),
                        "nsfr": float(s.nsfr),
                        "currency_breakdown": {k: float(v) for k, v in s.currency_breakdown.items()},
                        "intraday_min": float(s.intraday_min) if s.intraday_min else None,
                        "intraday_max": float(s.intraday_max) if s.intraday_max else None
                    } 
                    for date, s in self.snapshots.items()
                },
                "summary": self.get_liquidity_summary()
            }
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        elif format.lower() == 'csv':
            # Convert to DataFrame for CSV export
            rows = []
            for date, snapshot in sorted(self.snapshots.items()):
                row = {
                    "Date": date.isoformat(),
                    "Total Cash": float(snapshot.total_cash),
                    "HQLA": float(snapshot.high_quality_liquid_assets),
                    "Short Term Obligations": float(snapshot.short_term_obligations),
                    "LCR": float(snapshot.lcr),
                    "Stable Funding": float(snapshot.stable_funding),
                    "Required Stable Funding": float(snapshot.required_stable_funding),
                    "NSFR": float(snapshot.nsfr)
                }
                rows.append(row)
                
            df = pd.DataFrame(rows)
            df.to_csv(output_path, index=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
        logger.info(f"Dashboard data exported to {output_path}")
        return output_path

# Example usage
if __name__ == "__main__":
    # Create a dashboard
    dashboard = LiquidityDashboard("Example Bank")
    
    # Set total assets for reserve calculation
    dashboard.total_assets = Decimal('1000000000')  # $1 billion
    
    # Generate sample data for the past 90 days
    today = datetime.date.today()
    for i in range(90, 0, -1):
        date = today - datetime.timedelta(days=i)
        
        # Add some randomness to the data
        cash = Decimal(str(800000000 + np.random.normal(0, 10000000)))
        hqla = Decimal(str(600000000 + np.random.normal(0, 8000000)))
        short_term = Decimal(str(500000000 + np.random.normal(0, 5000000)))
        stable_funding = Decimal(str(750000000 + np.random.normal(0, 7000000)))
        required_stable_funding = Decimal(str(700000000 + np.random.normal(0, 6000000)))
        
        # Create a snapshot
        snapshot = LiquiditySnapshot(
            date=date,
            total_cash=cash,
            high_quality_liquid_assets=hqla,
            short_term_obligations=short_term,
            stable_funding=stable_funding,
            required_stable_funding=required_stable_funding,
            currency_breakdown={
                "USD": cash * Decimal('0.6'),
                "EUR": cash * Decimal('0.25'),
                "GBP": cash * Decimal('0.1'),
                "JPY": cash * Decimal('0.05')
            }
        )
        
        dashboard.add_snapshot(snapshot)
    
    # Get the latest snapshot
    latest = dashboard.get_latest_snapshot()
    if latest:
        print(f"Latest snapshot date: {latest.date}")
        print(f"LCR: {latest.lcr:.2f}")
        print(f"NSFR: {latest.nsfr:.2f}")
        
    # Get alerts
    alerts = dashboard.get_liquidity_alerts()
    for alert in alerts:
        print(f"ALERT: {alert}")
        
    # Generate charts
    charts_dir = Path("charts")
    charts_dir.mkdir(exist_ok=True)
    
    lcr_chart = dashboard.generate_lcr_nsfr_chart(output_path=str(charts_dir / "liquidity_ratios.png"))
    cash_chart = dashboard.generate_cash_position_chart(output_path=str(charts_dir / "cash_position.png"))
    currency_chart = dashboard.generate_currency_breakdown_chart(output_path=str(charts_dir / "currency_breakdown.png"))
    
    # Export dashboard data
    dashboard.export_dashboard_data(str(charts_dir / "dashboard_data.json"))
