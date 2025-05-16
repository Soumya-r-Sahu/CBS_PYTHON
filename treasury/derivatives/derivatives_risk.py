"""
Derivatives risk assessment module for treasury operations.

This module provides functionality for assessing and managing risk associated
with derivative positions, including risk metrics calculation, stress testing,
scenario analysis, and risk limits management.
"""

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
from decimal import Decimal
import logging
import math
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

# Local imports - assuming these modules are available
try:
    from treasury.derivatives.options_pricing import Option, OptionType
    from treasury.derivatives.swap_operations import SwapContract, SwapType
    from treasury.derivatives.futures_management import FuturesPosition, FuturesType
except ImportError:
    # For standalone usage during development
    pass

# Configure logging
logger = logging.getLogger(__name__)


class RiskMetricType(Enum):
    """Types of risk metrics for derivatives."""
    VALUE_AT_RISK = "value_at_risk"
    DELTA = "delta"
    GAMMA = "gamma"
    VEGA = "vega"
    THETA = "theta"
    RHO = "rho"
    DURATION = "duration"
    BASIS_RISK = "basis_risk"
    CORRELATION_RISK = "correlation_risk"
    SENSITIVITY = "rate_sensitivity"


class StressTestLevel(Enum):
    """Stress test severity levels."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"


@dataclass
class RiskLimit:
    """Represents a risk limit for derivatives."""
    
    metric: RiskMetricType
    limit_value: Decimal
    warning_threshold: Decimal  # Percentage of limit that triggers warning
    instrument_type: Optional[str] = None  # None for all instruments
    is_active: bool = True
    description: str = ""


@dataclass
class DerivativePosition:
    """Generic wrapper for any derivative position."""
    
    position_id: str
    instrument_type: str  # "option", "swap", "future", etc.
    instrument_details: Dict[str, Any]  # Instrument-specific details
    market_value: Decimal
    risk_metrics: Dict[str, Decimal] = field(default_factory=dict)
    underlying: Optional[str] = None
    counterparty: Optional[str] = None
    last_updated: datetime.datetime = field(default_factory=datetime.datetime.now)


@dataclass
class RiskReport:
    """Represents a risk report."""
    
    id: str
    report_date: datetime.date
    portfolio_value: Decimal
    risk_metrics: Dict[str, Dict[str, Union[Decimal, float]]]
    concentration_risks: List[Dict[str, Any]]
    limit_breaches: List[Dict[str, Any]]
    stress_test_results: Dict[str, Any]
    generated_by: str
    approved_by: Optional[str] = None
    comments: Optional[str] = None


class DerivativesRiskManager:
    """
    Manager for derivatives risk assessment.
    
    This class provides functionality for assessing and managing
    risk associated with derivative positions.
    """
    
    def __init__(self):
        """Initialize the derivatives risk manager."""
        self.positions: Dict[str, DerivativePosition] = {}
        self.risk_limits: List[RiskLimit] = []
        self.market_factors: Dict[str, Dict[str, float]] = {}
        self.correlations: Dict[str, Dict[str, float]] = {}
        self.risk_reports: List[RiskReport] = []
        self.scenarios: Dict[str, Dict[str, Any]] = {}
        
    def add_position(self, position: DerivativePosition) -> None:
        """
        Add a derivative position.
        
        Args:
            position: Derivative position
        """
        self.positions[position.position_id] = position
        logger.info(f"Added {position.instrument_type} position {position.position_id}")
        
    def remove_position(self, position_id: str) -> bool:
        """
        Remove a derivative position.
        
        Args:
            position_id: Position ID
            
        Returns:
            True if successful, False if position not found
        """
        if position_id in self.positions:
            del self.positions[position_id]
            logger.info(f"Removed position {position_id}")
            return True
        else:
            logger.warning(f"Position {position_id} not found")
            return False
            
    def update_position(self, position_id: str, 
                      updates: Dict[str, Any]) -> bool:
        """
        Update a derivative position.
        
        Args:
            position_id: Position ID
            updates: Dictionary of updates to apply
            
        Returns:
            True if successful, False if position not found
        """
        if position_id not in self.positions:
            logger.warning(f"Position {position_id} not found")
            return False
            
        position = self.positions[position_id]
        
        # Apply updates
        for key, value in updates.items():
            if key == "market_value":
                position.market_value = value
            elif key == "risk_metrics":
                for metric_name, metric_value in value.items():
                    position.risk_metrics[metric_name] = metric_value
            elif key == "instrument_details":
                for detail_key, detail_value in value.items():
                    position.instrument_details[detail_key] = detail_value
            elif hasattr(position, key):
                setattr(position, key, value)
                
        position.last_updated = datetime.datetime.now()
        
        logger.info(f"Updated position {position_id}")
        return True
        
    def get_position(self, position_id: str) -> Optional[DerivativePosition]:
        """
        Get a derivative position.
        
        Args:
            position_id: Position ID
            
        Returns:
            DerivativePosition if found, None otherwise
        """
        return self.positions.get(position_id)
        
    def set_risk_limit(self, 
                     metric: RiskMetricType,
                     limit_value: Decimal,
                     warning_threshold: Decimal,
                     instrument_type: Optional[str] = None,
                     description: str = "") -> None:
        """
        Set a risk limit.
        
        Args:
            metric: Risk metric type
            limit_value: Maximum allowed value
            warning_threshold: Threshold for warnings (as percentage)
            instrument_type: Instrument type or None for all instruments
            description: Description of the limit
        """
        # Remove any existing limit for this metric and instrument type
        self.risk_limits = [
            limit for limit in self.risk_limits
            if not (limit.metric == metric and limit.instrument_type == instrument_type)
        ]
        
        # Add new limit
        limit = RiskLimit(
            metric=metric,
            limit_value=limit_value,
            warning_threshold=warning_threshold,
            instrument_type=instrument_type,
            description=description
        )
        
        self.risk_limits.append(limit)
        
        logger.info(f"Set {metric.value} risk limit for " +
                    f"{instrument_type or 'all instruments'}: {limit_value}")
        
    def update_market_factor(self, 
                          factor_name: str,
                          values: Dict[str, float]) -> None:
        """
        Update market factor data.
        
        Args:
            factor_name: Name of the factor (e.g., "interest_rate", "volatility")
            values: Dictionary mapping keys (e.g., tenors, currencies) to values
        """
        self.market_factors[factor_name] = values
        logger.info(f"Updated market factor {factor_name}")
        
    def update_correlation(self, 
                          factor1: str,
                          factor2: str,
                          correlation: float) -> None:
        """
        Update correlation between two market factors.
        
        Args:
            factor1: First factor name
            factor2: Second factor name
            correlation: Correlation value (-1 to 1)
        """
        if factor1 not in self.correlations:
            self.correlations[factor1] = {}
            
        if factor2 not in self.correlations:
            self.correlations[factor2] = {}
            
        # Correlations are symmetric
        self.correlations[factor1][factor2] = correlation
        self.correlations[factor2][factor1] = correlation
        
        logger.info(f"Updated correlation between {factor1} and {factor2}: {correlation}")
        
    def calculate_portfolio_value(self) -> Decimal:
        """
        Calculate total portfolio market value.
        
        Returns:
            Total portfolio value
        """
        return sum(position.market_value for position in self.positions.values())
        
    def calculate_aggregate_risk_metrics(self) -> Dict[str, Decimal]:
        """
        Calculate aggregate risk metrics for the portfolio.
        
        Returns:
            Dictionary mapping risk metrics to aggregate values
        """
        aggregates = {}
        
        # Get all unique metrics
        all_metrics = set()
        for position in self.positions.values():
            all_metrics.update(position.risk_metrics.keys())
            
        # Calculate sums for each metric
        for metric in all_metrics:
            aggregates[metric] = sum(
                position.risk_metrics.get(metric, Decimal("0"))
                for position in self.positions.values()
            )
            
        # Special handling for portfolio VaR
        if "var_95" in all_metrics:
            # Apply diversification benefit (simplified)
            # In a real implementation, would use correlations
            portfolio_var = aggregates.get("var_95", Decimal("0"))
            aggregates["portfolio_var_95"] = portfolio_var * Decimal("0.8")  # 20% diversification
            
        return aggregates
        
    def check_risk_limits(self) -> List[Dict[str, Any]]:
        """
        Check if any risk metrics exceed defined limits.
        
        Returns:
            List of breaches with details
        """
        breaches = []
        
        # Calculate aggregate risk metrics
        aggregates = self.calculate_aggregate_risk_metrics()
        
        # Check each limit
        for limit in self.risk_limits:
            if not limit.is_active:
                continue
                
            # Convert metric name to expected format in aggregates
            metric_name = limit.metric.value.lower()
            
            # Check aggregate first
            if metric_name in aggregates:
                metric_value = aggregates[metric_name]
                limit_value = limit.limit_value
                warning_threshold = limit.warning_threshold
                
                if metric_value > limit_value:
                    breaches.append({
                        "metric": limit.metric.value,
                        "instrument_type": "portfolio",
                        "value": float(metric_value),
                        "limit": float(limit_value),
                        "excess": float(metric_value - limit_value),
                        "excess_percentage": float((metric_value / limit_value - 1) * 100),
                        "severity": "breach"
                    })
                    logger.warning(f"LIMIT BREACH: {limit.metric.value} for portfolio " +
                                  f"exceeded by {float(metric_value - limit_value):.2f}")
                    
                elif metric_value > limit_value * warning_threshold:
                    breaches.append({
                        "metric": limit.metric.value,
                        "instrument_type": "portfolio",
                        "value": float(metric_value),
                        "limit": float(limit_value),
                        "warning_threshold": float(limit_value * warning_threshold),
                        "severity": "warning"
                    })
                    logger.info(f"LIMIT WARNING: {limit.metric.value} for portfolio " +
                               f"approaching limit ({float(metric_value):.2f} vs {float(limit_value):.2f})")
            
            # Check individual instruments if limit applies to specific type
            if limit.instrument_type:
                for position in self.positions.values():
                    if position.instrument_type != limit.instrument_type:
                        continue
                        
                    if metric_name in position.risk_metrics:
                        metric_value = position.risk_metrics[metric_name]
                        limit_value = limit.limit_value
                        warning_threshold = limit.warning_threshold
                        
                        if metric_value > limit_value:
                            breaches.append({
                                "metric": limit.metric.value,
                                "position_id": position.position_id,
                                "instrument_type": position.instrument_type,
                                "value": float(metric_value),
                                "limit": float(limit_value),
                                "excess": float(metric_value - limit_value),
                                "excess_percentage": float((metric_value / limit_value - 1) * 100),
                                "severity": "breach"
                            })
                            logger.warning(f"LIMIT BREACH: {limit.metric.value} for " +
                                         f"{position.instrument_type} position {position.position_id} " +
                                         f"exceeded by {float(metric_value - limit_value):.2f}")
                            
                        elif metric_value > limit_value * warning_threshold:
                            breaches.append({
                                "metric": limit.metric.value,
                                "position_id": position.position_id,
                                "instrument_type": position.instrument_type,
                                "value": float(metric_value),
                                "limit": float(limit_value),
                                "warning_threshold": float(limit_value * warning_threshold),
                                "severity": "warning"
                            })
                            logger.info(f"LIMIT WARNING: {limit.metric.value} for " +
                                      f"{position.instrument_type} position {position.position_id} " +
                                      f"approaching limit ({float(metric_value):.2f} vs {float(limit_value):.2f})")
        
        return breaches
        
    def calculate_value_at_risk(self,
                             confidence_level: float = 0.95,
                             time_horizon: int = 1) -> Dict[str, Any]:
        """
        Calculate Value at Risk (VaR) for the derivative portfolio.
        
        Args:
            confidence_level: Confidence level (e.g., 0.95, 0.99)
            time_horizon: Time horizon in days
            
        Returns:
            Dictionary with VaR details
        """
        if not self.positions:
            return {
                "var": 0.0,
                "confidence_level": confidence_level,
                "time_horizon": time_horizon,
                "method": "parametric",
                "total_portfolio_value": 0.0
            }
            
        # Extract positions with value and risk metrics
        positions_data = []
        for position in self.positions.values():
            if "delta" not in position.risk_metrics:
                continue
                
            positions_data.append({
                "id": position.position_id,
                "type": position.instrument_type,
                "value": float(position.market_value),
                "delta": float(position.risk_metrics.get("delta", 0)),
                "gamma": float(position.risk_metrics.get("gamma", 0)),
                "underlying": position.underlying
            })
            
        # Group by underlying
        underlyings = {}
        for position in positions_data:
            underlying = position["underlying"] or "unknown"
            if underlying not in underlyings:
                underlyings[underlying] = {
                    "positions": [],
                    "total_delta": 0,
                    "total_gamma": 0,
                    "total_value": 0
                }
                
            group = underlyings[underlying]
            group["positions"].append(position)
            group["total_delta"] += position["delta"]
            group["total_gamma"] += position["gamma"]
            group["total_value"] += position["value"]
            
        # Calculate VaR assuming 1% daily volatility (simplified)
        # In a real implementation, would use historical volatility data
        daily_volatility = 0.01
        volatility = daily_volatility * math.sqrt(time_horizon)
        
        # Get z-score for confidence level
        z_score = stats.norm.ppf(confidence_level)
        
        # Calculate parametric VaR
        total_var = 0
        total_value = 0
        
        for underlying, data in underlyings.items():
            # First-order approximation (delta)
            delta_var = abs(data["total_delta"]) * volatility * z_score
            
            # Second-order correction (gamma)
            gamma_var = 0.5 * abs(data["total_gamma"]) * (volatility ** 2)
            
            # Total VaR for this underlying
            underlying_var = delta_var + gamma_var
            total_var += underlying_var
            total_value += data["total_value"]
            
        # Apply correlation adjustment (simplified)
        # In a real implementation, would use correlation matrix
        if len(underlyings) > 1:
            # Assume 0.5 correlation between all underlyings
            correlation_adjustment = 0.7
            total_var *= correlation_adjustment
            
        return {
            "var": float(total_var),
            "confidence_level": confidence_level,
            "time_horizon": time_horizon,
            "method": "parametric",
            "total_portfolio_value": float(total_value),
            "var_percent": (float(total_var) / float(total_value)) * 100 if total_value > 0 else 0
        }
        
    def define_stress_scenario(self,
                            scenario_name: str,
                            description: str,
                            market_moves: Dict[str, Dict[str, float]]) -> None:
        """
        Define a stress testing scenario.
        
        Args:
            scenario_name: Name of the scenario
            description: Description of the scenario
            market_moves: Dictionary mapping factors to moves
                         {"interest_rate": {"1Y": 0.01, "5Y": 0.015}, 
                          "volatility": {"equity": 0.10}}
        """
        self.scenarios[scenario_name] = {
            "description": description,
            "market_moves": market_moves,
            "created_at": datetime.datetime.now()
        }
        
        logger.info(f"Defined stress scenario: {scenario_name}")
        
    def run_stress_test(self, 
                      scenario_name: str,
                      custom_moves: Optional[Dict[str, Dict[str, float]]] = None) -> Dict[str, Any]:
        """
        Run a stress test using a predefined or custom scenario.
        
        Args:
            scenario_name: Name of the scenario
            custom_moves: Optional custom market moves to override the scenario
            
        Returns:
            Dictionary with stress test results
        """
        # Get scenario
        if scenario_name not in self.scenarios and not custom_moves:
            logger.warning(f"Scenario {scenario_name} not found")
            return {"error": "Scenario not found"}
            
        # Use custom moves if provided, otherwise use scenario moves
        market_moves = custom_moves if custom_moves else self.scenarios[scenario_name]["market_moves"]
        
        # Calculate base portfolio value
        base_value = float(self.calculate_portfolio_value())
        
        # Calculate stressed values for each position
        position_impacts = []
        total_stressed_value = 0
        
        for position in self.positions.values():
            # Apply stress based on position type and sensitivity
            stressed_value = self._calculate_stressed_position_value(position, market_moves)
            value_change = stressed_value - float(position.market_value)
            percent_change = (value_change / float(position.market_value)) * 100 if position.market_value != 0 else 0
            
            position_impacts.append({
                "position_id": position.position_id,
                "instrument_type": position.instrument_type,
                "original_value": float(position.market_value),
                "stressed_value": stressed_value,
                "absolute_change": value_change,
                "percent_change": percent_change
            })
            
            total_stressed_value += stressed_value
            
        # Calculate overall impact
        total_change = total_stressed_value - base_value
        total_percent_change = (total_change / base_value) * 100 if base_value > 0 else 0
        
        return {
            "scenario_name": scenario_name,
            "base_portfolio_value": base_value,
            "stressed_portfolio_value": total_stressed_value,
            "absolute_change": total_change,
            "percent_change": total_percent_change,
            "position_impacts": position_impacts,
            "run_at": datetime.datetime.now().isoformat()
        }
        
    def _calculate_stressed_position_value(self,
                                         position: DerivativePosition,
                                         market_moves: Dict[str, Dict[str, float]]) -> float:
        """
        Calculate stressed value of a position.
        
        Args:
            position: Derivative position
            market_moves: Dictionary mapping factors to moves
            
        Returns:
            Stressed position value
        """
        current_value = float(position.market_value)
        
        # Apply stress based on instrument type
        if position.instrument_type == "option":
            # Use Greeks for options
            price_impact = 0
            
            # Delta impact (underlying price changes)
            if "equity_price" in market_moves and position.underlying in market_moves["equity_price"]:
                price_change = market_moves["equity_price"][position.underlying]
                delta = float(position.risk_metrics.get("delta", 0))
                gamma = float(position.risk_metrics.get("gamma", 0))
                
                # First-order approximation (delta)
                delta_impact = delta * price_change
                
                # Second-order correction (gamma)
                gamma_impact = 0.5 * gamma * (price_change ** 2)
                
                price_impact = delta_impact + gamma_impact
                
            # Vega impact (volatility changes)
            vega_impact = 0
            if "volatility" in market_moves:
                vol_category = "equity" if position.underlying else "unknown"
                if vol_category in market_moves["volatility"]:
                    vol_change = market_moves["volatility"][vol_category]
                    vega = float(position.risk_metrics.get("vega", 0))
                    vega_impact = vega * vol_change
                    
            # Theta impact (time decay)
            theta_impact = 0
            theta = float(position.risk_metrics.get("theta", 0))
            theta_impact = theta * 1  # Assume 1 day
            
            # Rho impact (interest rate changes)
            rho_impact = 0
            if "interest_rate" in market_moves and "1Y" in market_moves["interest_rate"]:
                rate_change = market_moves["interest_rate"]["1Y"]
                rho = float(position.risk_metrics.get("rho", 0))
                rho_impact = rho * rate_change
                
            # Total impact
            total_impact = price_impact + vega_impact + theta_impact + rho_impact
            return current_value + total_impact
            
        elif position.instrument_type == "swap":
            # Use DV01 for swaps
            if "interest_rate" in market_moves:
                # Find applicable rate change based on tenor
                tenor = position.instrument_details.get("tenor", "5Y")
                tenor_key = tenor[:tenor.index("Y")] if "Y" in tenor else "1Y"
                
                if tenor_key in market_moves["interest_rate"]:
                    rate_change = market_moves["interest_rate"][tenor_key]
                    dv01 = float(position.risk_metrics.get("dv01", 0))
                    impact = dv01 * rate_change * 10000  # DV01 is for 1bp, convert to actual move
                    return current_value + impact
                    
            # If no applicable market moves, return unchanged
            return current_value
            
        elif position.instrument_type == "future":
            # Use simple sensitivity for futures
            if "future_price" in market_moves:
                contract_type = position.instrument_details.get("futures_type", "unknown")
                
                if contract_type in market_moves["future_price"]:
                    price_change = market_moves["future_price"][contract_type]
                    quantity = position.instrument_details.get("quantity", 0)
                    contract_size = position.instrument_details.get("contract_size", 1)
                    
                    impact = quantity * contract_size * price_change
                    return current_value + impact
            
            # If no applicable market moves, return unchanged
            return current_value
            
        else:
            # Default: assume no impact for unknown types
            return current_value
            
    def calculate_concentration_risk(self) -> List[Dict[str, Any]]:
        """
        Calculate concentration risks in the portfolio.
        
        Returns:
            List of concentration risk details
        """
        # Calculate portfolio value
        portfolio_value = float(self.calculate_portfolio_value())
        if portfolio_value == 0:
            return []
            
        # Group by different dimensions
        concentrations = {
            "instrument_type": {},
            "underlying": {},
            "counterparty": {}
        }
        
        for position in self.positions.values():
            # By instrument type
            instrument_type = position.instrument_type
            if instrument_type not in concentrations["instrument_type"]:
                concentrations["instrument_type"][instrument_type] = 0
                
            concentrations["instrument_type"][instrument_type] += float(position.market_value)
            
            # By underlying
            underlying = position.underlying or "unknown"
            if underlying not in concentrations["underlying"]:
                concentrations["underlying"][underlying] = 0
                
            concentrations["underlying"][underlying] += float(position.market_value)
            
            # By counterparty
            counterparty = position.counterparty or "unknown"
            if counterparty not in concentrations["counterparty"]:
                concentrations["counterparty"][counterparty] = 0
                
            concentrations["counterparty"][counterparty] += float(position.market_value)
            
        # Find significant concentrations (>10% of portfolio)
        results = []
        threshold = portfolio_value * 0.1  # 10% threshold
        
        for dim, values in concentrations.items():
            for key, value in sorted(values.items(), key=lambda x: x[1], reverse=True):
                percentage = (value / portfolio_value) * 100
                
                if value > threshold:
                    results.append({
                        "dimension": dim,
                        "category": key,
                        "value": value,
                        "percentage": percentage
                    })
                    
        return results
        
    def generate_risk_report(self) -> RiskReport:
        """
        Generate a comprehensive risk report.
        
        Returns:
            Risk report
        """
        # Calculate all risk metrics
        var_95 = self.calculate_value_at_risk(confidence_level=0.95)
        var_99 = self.calculate_value_at_risk(confidence_level=0.99)
        
        aggregates = self.calculate_aggregate_risk_metrics()
        
        # Check for limit breaches
        limit_breaches = self.check_risk_limits()
        
        # Calculate concentration risks
        concentration_risks = self.calculate_concentration_risk()
        
        # Run stress tests for all scenarios
        stress_results = {}
        for scenario_name in self.scenarios.keys():
            stress_results[scenario_name] = self.run_stress_test(scenario_name)
            
        # Create report
        report_id = f"RISK-{datetime.date.today().isoformat()}"
        
        report = RiskReport(
            id=report_id,
            report_date=datetime.date.today(),
            portfolio_value=Decimal(str(self.calculate_portfolio_value())),
            risk_metrics={
                "var": {
                    "var_95": var_95["var"],
                    "var_95_percent": var_95["var_percent"],
                    "var_99": var_99["var"],
                    "var_99_percent": var_99["var_percent"],
                },
                "greeks": {
                    metric: float(value) 
                    for metric, value in aggregates.items()
                    if metric in ["delta", "gamma", "vega", "theta", "rho"]
                },
                "rates": {
                    metric: float(value)
                    for metric, value in aggregates.items()
                    if metric in ["dv01", "duration", "convexity"]
                }
            },
            concentration_risks=concentration_risks,
            limit_breaches=limit_breaches,
            stress_test_results=stress_results,
            generated_by="DerivativesRiskManager"
        )
        
        self.risk_reports.append(report)
        
        logger.info(f"Generated risk report {report_id}")
        return report
        
    def format_risk_report(self, report: RiskReport, format: str = "text") -> str:
        """
        Format a risk report.
        
        Args:
            report: Risk report
            format: Output format ('text', 'html', etc.)
            
        Returns:
            Formatted report
        """
        if format.lower() == "text":
            # Create text report
            lines = []
            
            # Header
            lines.append(f"DERIVATIVES RISK REPORT: {report.report_date.isoformat()}")
            lines.append("=" * 50)
            lines.append("")
            
            # Portfolio summary
            lines.append(f"Portfolio Value: {float(report.portfolio_value):,.2f}")
            lines.append("")
            
            # VaR
            lines.append("Value at Risk (VaR)")
            lines.append("-" * 20)
            lines.append(f"95% 1-Day VaR: {report.risk_metrics['var']['var_95']:,.2f} " +
                        f"({report.risk_metrics['var']['var_95_percent']:.2f}%)")
            lines.append(f"99% 1-Day VaR: {report.risk_metrics['var']['var_99']:,.2f} " +
                        f"({report.risk_metrics['var']['var_99_percent']:.2f}%)")
            lines.append("")
            
            # Greeks
            lines.append("Aggregate Risk Sensitivities")
            lines.append("-" * 30)
            for metric, value in report.risk_metrics["greeks"].items():
                if value != 0:
                    lines.append(f"{metric.capitalize()}: {value:,.2f}")
            lines.append("")
            
            # Rate sensitivities
            if report.risk_metrics["rates"]:
                lines.append("Interest Rate Sensitivities")
                lines.append("-" * 30)
                for metric, value in report.risk_metrics["rates"].items():
                    if value != 0:
                        if metric == "dv01":
                            lines.append(f"DV01: {value:,.2f}")
                        else:
                            lines.append(f"{metric.capitalize()}: {value:,.4f}")
                lines.append("")
            
            # Concentration risks
            if report.concentration_risks:
                lines.append("Concentration Risks")
                lines.append("-" * 20)
                for risk in sorted(report.concentration_risks, 
                                 key=lambda x: x["percentage"], reverse=True)[:5]:
                    lines.append(f"{risk['dimension'].capitalize()} - {risk['category']}: " +
                                f"{risk['value']:,.2f} ({risk['percentage']:.1f}%)")
                lines.append("")
                
            # Limit breaches
            if report.limit_breaches:
                lines.append("Risk Limit Breaches")
                lines.append("-" * 20)
                breaches = [b for b in report.limit_breaches if b["severity"] == "breach"]
                warnings = [b for b in report.limit_breaches if b["severity"] == "warning"]
                
                if breaches:
                    lines.append("BREACHES:")
                    for breach in breaches:
                        lines.append(f"  {breach['metric']} - {breach.get('position_id', 'Portfolio')}: " +
                                    f"{breach['value']:,.2f} vs limit {breach['limit']:,.2f} " +
                                    f"(+{breach['excess']:,.2f}, {breach['excess_percentage']:.1f}%)")
                        
                if warnings:
                    lines.append("WARNINGS:")
                    for warning in warnings:
                        lines.append(f"  {warning['metric']} - {warning.get('position_id', 'Portfolio')}: " +
                                    f"{warning['value']:,.2f} approaching limit {warning['limit']:,.2f}")
                lines.append("")
                
            # Stress tests
            if report.stress_test_results:
                lines.append("Stress Test Results")
                lines.append("-" * 20)
                
                for scenario, result in report.stress_test_results.items():
                    if "error" in result:
                        continue
                        
                    lines.append(f"Scenario: {scenario}")
                    lines.append(f"  Impact: {result['absolute_change']:,.2f} ({result['percent_change']:.2f}%)")
                    
                    # Top 3 most impacted positions
                    if result.get("position_impacts"):
                        sorted_impacts = sorted(result["position_impacts"], 
                                              key=lambda x: abs(x["percent_change"]), 
                                              reverse=True)
                        
                        if sorted_impacts:
                            lines.append("  Most impacted positions:")
                            for impact in sorted_impacts[:3]:
                                lines.append(f"    {impact['instrument_type']} {impact['position_id']}: " +
                                           f"{impact['absolute_change']:,.2f} ({impact['percent_change']:.2f}%)")
                    
                    lines.append("")
                
            # Footer
            lines.append("-" * 50)
            lines.append(f"Generated by: {report.generated_by}")
            lines.append(f"Report ID: {report.id}")
            
            if report.comments:
                lines.append("")
                lines.append("COMMENTS")
                lines.append(report.comments)
                
            return "\n".join(lines)
            
        else:
            # Default format
            return f"Risk Report {report.id} - {report.report_date.isoformat()}"


def create_option_position_from_option(
    option_id: str,
    option: Option,
    quantity: int,
    spot_price: float,
    risk_free_rate: float,
    volatility: float,
    option_price: float,
    counterparty: str = "Internal"
) -> DerivativePosition:
    """
    Create a derivative position from an option.
    
    Args:
        option_id: Option ID
        option: Option object
        quantity: Number of options (positive for long, negative for short)
        spot_price: Current price of the underlying
        risk_free_rate: Risk-free rate
        volatility: Implied volatility
        option_price: Market price of the option
        counterparty: Counterparty name
        
    Returns:
        DerivativePosition for the option
    """
    # Calculate Greeks using Black-Scholes
    from treasury.derivatives.options_pricing import BlackScholes
    
    greeks = BlackScholes.price_option(
        option=option,
        spot_price=spot_price,
        risk_free_rate=risk_free_rate,
        volatility=volatility
    )
    
    # Calculate market value
    contract_size = option.contract_size
    market_value = quantity * option_price * contract_size
    
    # Create position with risk metrics
    position = DerivativePosition(
        position_id=option_id,
        instrument_type="option",
        instrument_details={
            "option_type": option.option_type.value,
            "style": option.style.value,
            "strike_price": float(option.strike_price),
            "expiry_date": option.expiry_date.isoformat(),
            "contract_size": contract_size,
            "days_to_expiry": option.days_to_expiry,
            "quantity": quantity
        },
        market_value=Decimal(str(market_value)),
        risk_metrics={
            "delta": Decimal(str(greeks["delta"] * quantity * contract_size)),
            "gamma": Decimal(str(greeks["gamma"] * quantity * contract_size)),
            "vega": Decimal(str(greeks["vega"] * quantity * contract_size)),
            "theta": Decimal(str(greeks["theta"] * quantity * contract_size)),
            "rho": Decimal(str(greeks["rho"] * quantity * contract_size)),
            "var_95": Decimal(str(abs(market_value) * 0.1))  # Simplified VaR calculation
        },
        underlying=option.underlying,
        counterparty=counterparty
    )
    
    return position


def create_swap_position_from_swap(
    swap_id: str,
    swap: SwapContract,
    market_value: float,
    risk_metrics: Dict[str, float],
    counterparty: Optional[str] = None
) -> DerivativePosition:
    """
    Create a derivative position from a swap.
    
    Args:
        swap_id: Swap ID
        swap: SwapContract object
        market_value: Current market value of the swap
        risk_metrics: Dictionary of risk metrics for the swap
        counterparty: Counterparty name (use from swap if None)
        
    Returns:
        DerivativePosition for the swap
    """
    # Extract details from swap
    swap_details = {
        "swap_type": swap.swap_type.value,
        "effective_date": swap.effective_date.isoformat(),
        "maturity_date": swap.maturity_date.isoformat(),
        "tenor": swap.tenor,
        "remaining_tenor": swap.remaining_tenor,
        "legs": []
    }
    
    # Add leg details
    for idx, leg in enumerate(swap.legs):
        swap_details["legs"].append({
            "leg": idx + 1,
            "currency": leg.currency,
            "is_fixed": leg.is_fixed,
            "notional": float(leg.notional_amount),
            "rate": str(leg.rate),
            "payment_freq": leg.payment_frequency.value
        })
        
    # Create position with risk metrics
    position = DerivativePosition(
        position_id=swap_id,
        instrument_type="swap",
        instrument_details=swap_details,
        market_value=Decimal(str(market_value)),
        risk_metrics={metric: Decimal(str(value)) for metric, value in risk_metrics.items()},
        underlying=None,  # Swaps don't have a direct underlying like options
        counterparty=counterparty or swap.counterparty
    )
    
    return position


def create_future_position_from_future(
    position_id: str,
    future_position: FuturesPosition
) -> DerivativePosition:
    """
    Create a derivative position from a futures position.
    
    Args:
        position_id: Position ID
        future_position: FuturesPosition object
        
    Returns:
        DerivativePosition for the future
    """
    contract = future_position.contract
    
    # Extract details
    future_details = {
        "futures_type": contract.futures_type.value,
        "ticker": contract.ticker,
        "contract_month": contract.contract_month,
        "quantity": future_position.quantity,
        "contract_size": contract.contract_size,
        "expiry_date": contract.expiry_date.isoformat(),
        "days_to_expiry": contract.days_to_expiry
    }
    
    # Calculate risk metrics
    notional_value = float(future_position.notional_value)
    
    # Simplified risk metrics for futures
    risk_metrics = {
        "delta": Decimal(str(notional_value)),  # Futures have delta of 1
        "var_95": Decimal(str(notional_value * 0.04)),  # Simplified 95% 1-day VaR (4%)
        "dv01": Decimal("0")  # Default to 0, will be non-zero for interest rate futures
    }
    
    # Add DV01 for interest rate futures
    if contract.futures_type == FuturesType.INTEREST_RATE:
        # Simple approximation based on contract size
        if "treasury" in contract.ticker.lower():
            # Treasury futures - higher DV01
            risk_metrics["dv01"] = Decimal(str(notional_value * 0.01 / 100))
        else:
            # Other interest rate futures
            risk_metrics["dv01"] = Decimal(str(notional_value * 0.0025 / 100))
    
    # Create position
    position = DerivativePosition(
        position_id=position_id,
        instrument_type="future",
        instrument_details=future_details,
        market_value=future_position.unrealized_pnl,  # For futures, market value is the unrealized P&L
        risk_metrics=risk_metrics,
        underlying=contract.ticker,
        counterparty=contract.exchange
    )
    
    return position


# Example usage
if __name__ == "__main__":
    # Create risk manager
    risk_manager = DerivativesRiskManager()
    
    # Set risk limits
    risk_manager.set_risk_limit(
        RiskMetricType.VALUE_AT_RISK,
        Decimal("500000"),
        Decimal("0.8"),
        description="Maximum portfolio VaR"
    )
    
    risk_manager.set_risk_limit(
        RiskMetricType.DELTA,
        Decimal("2000000"),
        Decimal("0.8"),
        description="Maximum portfolio delta exposure"
    )
    
    risk_manager.set_risk_limit(
        RiskMetricType.VEGA,
        Decimal("50000"),
        Decimal("0.8"),
        instrument_type="option",
        description="Maximum vega exposure for options"
    )
    
    # Create some sample derivative positions
    # Example 1: Option position
    option_position = DerivativePosition(
        position_id="OPT123",
        instrument_type="option",
        instrument_details={
            "option_type": "call",
            "style": "european",
            "strike_price": 100.0,
            "expiry_date": (datetime.date.today() + datetime.timedelta(days=30)).isoformat(),
            "contract_size": 100,
            "quantity": 100
        },
        market_value=Decimal("50000"),
        risk_metrics={
            "delta": Decimal("30000"),
            "gamma": Decimal("5000"),
            "vega": Decimal("15000"),
            "theta": Decimal("-1000"),
            "rho": Decimal("2000"),
            "var_95": Decimal("5000")
        },
        underlying="AAPL",
        counterparty="Broker A"
    )
    
    # Example 2: Swap position
    swap_position = DerivativePosition(
        position_id="SWAP456",
        instrument_type="swap",
        instrument_details={
            "swap_type": "interest_rate",
            "effective_date": datetime.date.today().isoformat(),
            "maturity_date": (datetime.date.today() + datetime.timedelta(days=365*5)).isoformat(),
            "tenor": "5Y",
            "notional": 10000000.0
        },
        market_value=Decimal("100000"),
        risk_metrics={
            "dv01": Decimal("5000"),
            "duration": Decimal("4.5"),
            "var_95": Decimal("20000")
        },
        counterparty="Bank XYZ"
    )
    
    # Example 3: Futures position
    future_position = DerivativePosition(
        position_id="FUT789",
        instrument_type="future",
        instrument_details={
            "futures_type": "interest_rate",
            "ticker": "ZN",
            "contract_month": "DEC-23",
            "quantity": 10,
            "contract_size": 100000
        },
        market_value=Decimal("15000"),
        risk_metrics={
            "delta": Decimal("1000000"),
            "var_95": Decimal("40000"),
            "dv01": Decimal("2500")
        },
        underlying="US 10Y Treasury",
        counterparty="CME"
    )
    
    # Add positions to manager
    risk_manager.add_position(option_position)
    risk_manager.add_position(swap_position)
    risk_manager.add_position(future_position)
    
    # Define stress scenarios
    risk_manager.define_stress_scenario(
        "interest_rate_up",
        "Parallel upward shift of interest rate curve by 100 bps",
        {
            "interest_rate": {
                "1Y": 0.01,
                "2Y": 0.01,
                "5Y": 0.01,
                "10Y": 0.01
            }
        }
    )
    
    risk_manager.define_stress_scenario(
        "market_crash",
        "Severe equity market crash with volatility spike",
        {
            "equity_price": {
                "AAPL": -0.20,
                "S&P500": -0.15
            },
            "volatility": {
                "equity": 0.15
            },
            "interest_rate": {
                "1Y": -0.005,
                "5Y": -0.01
            }
        }
    )
    
    # Calculate portfolio metrics
    portfolio_value = risk_manager.calculate_portfolio_value()
    print(f"Portfolio value: {float(portfolio_value):,.2f}")
    
    # Calculate VaR
    var = risk_manager.calculate_value_at_risk()
    print(f"95% 1-day VaR: {var['var']:,.2f} ({var['var_percent']:.2f}%)")
    
    # Check risk limits
    breaches = risk_manager.check_risk_limits()
    if breaches:
        print("\nRisk limit breaches:")
        for breach in breaches:
            print(f"  {breach['metric']} - {breach.get('position_id', 'Portfolio')}: " +
                 f"{breach['value']:,.2f} vs limit {breach['limit']:,.2f}")
    
    # Run stress test
    stress_result = risk_manager.run_stress_test("market_crash")
    print(f"\nStress test - {stress_result['scenario_name']}:")
    print(f"  Impact: {stress_result['absolute_change']:,.2f} ({stress_result['percent_change']:.2f}%)")
    
    # Generate risk report
    report = risk_manager.generate_risk_report()
    report_text = risk_manager.format_risk_report(report)
    
    print("\n" + "=" * 50)
    print("RISK REPORT SUMMARY")
    print("=" * 50)
    print(report_text)
