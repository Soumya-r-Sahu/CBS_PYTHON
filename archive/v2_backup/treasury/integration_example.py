"""
Treasury Integration Example.

This script demonstrates how to use various components of the Treasury module together,
including bonds management, liquidity monitoring, forex operations, derivatives,
and integration with risk compliance.
"""

import os
import sys
import datetime
from decimal import Decimal
import logging
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


# Import treasury modules
from treasury.config import get_config
from treasury.bonds.bond_portfolio import Bond, BondPosition, BondPortfolio
from treasury.bonds.bond_valuation import BondValuation, YieldCurve, CashFlow
from treasury.liquidity_management.liquidity_dashboard import LiquiditySnapshot, LiquidityDashboard
from treasury.forex.forex_trading import FxTrade, FxTradeManager
from treasury.forex.forex_settlement import Settlement, FxSettlementManager, SettlementStatus
from treasury.forex.forex_risk import ForexRiskManager, RiskMetricType as FxRiskMetricType
from treasury.derivatives.options_pricing import Option, OptionType, OptionStyle, BlackScholes
from treasury.derivatives.swap_operations import (
    SwapContract, SwapLeg, SwapType, SwapManager,
    PaymentFrequency, DayCountConvention
)
from treasury.derivatives.futures_management import (
    FuturesContract, FuturesPosition, FuturesType, FuturesManager
)
from treasury.derivatives.derivatives_risk import (
    DerivativesRiskManager, DerivativePosition, 
    RiskMetricType, create_option_position_from_option,
    create_swap_position_from_swap, create_future_position_from_future
)

# Import risk-compliance module if available
try:
    from risk_compliance.audit_trail import audit_trail_manager
    from risk_compliance.fraud_detection import transaction_monitor
    from risk_compliance.regulatory_reporting import regulatory_reporting_system
    risk_compliance_available = True
except ImportError:
    logger.warning("Risk-compliance module not available. Some features will be disabled.")
    risk_compliance_available = False


def setup_bond_portfolio():
    """Set up a sample bond portfolio."""
    logger.info("Setting up bond portfolio...")
    
    # Create a portfolio
    portfolio = BondPortfolio("Treasury Bond Portfolio", "USD")
    
    # Create a few bonds
    bonds = [
        Bond(
            id="UST5Y",
            isin="US912828YM69",
            cusip="912828YM6",
            issuer="US Treasury",
            issue_date=datetime.date(2022, 5, 15),
            maturity_date=datetime.date(2027, 5, 15),
            coupon_rate=Decimal('2.75'),
            face_value=Decimal('1000'),
            currency="USD",
            bond_type="government",
            payment_frequency=2,
            day_count_convention="actual/actual"
        ),
        Bond(
            id="UST10Y",
            isin="US912810TW33",
            cusip="912810TW3",
            issuer="US Treasury",
            issue_date=datetime.date(2022, 2, 15),
            maturity_date=datetime.date(2032, 2, 15),
            coupon_rate=Decimal('2.25'),
            face_value=Decimal('1000'),
            currency="USD",
            bond_type="government",
            payment_frequency=2,
            day_count_convention="actual/actual"
        ),
        Bond(
            id="CORP-AAPL",
            isin="US037833DT06",
            cusip="037833DT0",
            issuer="Apple Inc",
            issue_date=datetime.date(2021, 8, 20),
            maturity_date=datetime.date(2026, 8, 20),
            coupon_rate=Decimal('3.20'),
            face_value=Decimal('1000'),
            currency="USD",
            bond_type="corporate",
            payment_frequency=2,
            day_count_convention="30/360"
        ),
    ]
    
    # Add positions to the portfolio
    positions = [
        BondPosition(
            bond=bonds[0],
            quantity=5000,
            acquisition_date=datetime.date(2022, 6, 10),
            acquisition_price=Decimal('98.75'),
            acquisition_yield=Decimal('3.05')
        ),
        BondPosition(
            bond=bonds[1],
            quantity=3000,
            acquisition_date=datetime.date(2022, 3, 5),
            acquisition_price=Decimal('97.50'),
            acquisition_yield=Decimal('2.45')
        ),
        BondPosition(
            bond=bonds[2],
            quantity=2000,
            acquisition_date=datetime.date(2021, 9, 15),
            acquisition_price=Decimal('99.80'),
            acquisition_yield=Decimal('3.25')
        ),
    ]
    
    for position in positions:
        portfolio.add_position(position)
    
    return portfolio, bonds


def analyze_bond_portfolio(portfolio, bonds):
    """Perform analysis on bond portfolio."""
    logger.info("Analyzing bond portfolio...")
    
    # Create a yield curve for valuation
    curve = YieldCurve("USD", datetime.date.today())
    curve.add_point(0.25, Decimal("3.95"))
    curve.add_point(0.50, Decimal("4.05"))
    curve.add_point(1.0, Decimal("4.15"))
    curve.add_point(2.0, Decimal("4.25"))
    curve.add_point(3.0, Decimal("4.30"))
    curve.add_point(5.0, Decimal("4.40"))
    curve.add_point(7.0, Decimal("4.45"))
    curve.add_point(10.0, Decimal("4.50"))
    curve.add_point(20.0, Decimal("4.60"))
    curve.add_point(30.0, Decimal("4.65"))
    
    # Get current market prices using the yield curve
    market_prices = {}
    for bond_id in portfolio.positions:
        position = portfolio.positions[bond_id]
        bond = position.bond
        
        # Calculate years to maturity
        years_to_maturity = (bond.maturity_date - datetime.date.today()).days / 365.0
        
        # Get yield from curve
        bond_yield = curve.get_yield(years_to_maturity)
        
        # Calculate cash flows
        cash_flows = BondValuation.calculate_cash_flows(
            bond.issue_date, bond.maturity_date, bond.face_value, 
            bond.coupon_rate, bond.payment_frequency
        )
        
        # Calculate price
        price = BondValuation.price_bond_from_yield(cash_flows, bond_yield)
        market_prices[bond_id] = price
        
        # Calculate risk metrics
        macaulay_duration, modified_duration = BondValuation.calculate_duration(
            cash_flows, bond_yield
        )
        convexity = BondValuation.calculate_convexity(cash_flows, bond_yield)
        
        logger.info(f"Bond {bond.id} ({bond.issuer}): Price={price}%, "
                   f"Duration={modified_duration:.2f}, Convexity={convexity:.2f}")
    
    # Calculate portfolio value and performance
    portfolio_value = portfolio.calculate_portfolio_value(datetime.date.today(), market_prices)
    performance = portfolio.get_performance_summary(market_prices)
    
    logger.info(f"Portfolio value: ${portfolio_value}")
    logger.info(f"Performance: ROI={performance['return_on_investment_pct']:.2f}%, "
               f"Unrealized G/L=${performance['unrealized_gain_loss']}")
    
    # Get exposure by issuer
    exposure = portfolio.get_bond_exposure_by_issuer()
    for issuer, amount in exposure.items():
        logger.info(f"Exposure to {issuer}: ${amount}")
        
    # Get maturity distribution
    maturity_dist = portfolio.get_maturity_distribution()
    for bucket, amount in maturity_dist.items():
        logger.info(f"Maturity bucket {bucket}: ${amount}")
    
    return market_prices


def setup_liquidity_dashboard():
    """Set up a sample liquidity dashboard."""
    logger.info("Setting up liquidity dashboard...")
    
    # Create a dashboard
    dashboard = LiquidityDashboard("Example Bank")
    
    # Set total assets
    dashboard.total_assets = Decimal('1000000000')  # $1 billion
    
    # Generate data for the past 30 days
    today = datetime.date.today()
    for i in range(30, 0, -1):
        date = today - datetime.timedelta(days=i)
        
        # Create sample data with slight variations
        # In a real system, this would come from database or API
        base_cash = Decimal('150000000')  # $150 million
        base_hqla = Decimal('120000000')  # $120 million
        base_short_term = Decimal('100000000')  # $100 million
        base_stable = Decimal('180000000')  # $180 million
        base_required = Decimal('160000000')  # $160 million
        
        # Add some day-to-day variation to simulate real data
        variation = lambda: Decimal(str(1 + (0.02 * (0.5 - i/60))))
        
        # Create snapshot
        snapshot = LiquiditySnapshot(
            date=date,
            total_cash=base_cash * variation(),
            high_quality_liquid_assets=base_hqla * variation(),
            short_term_obligations=base_short_term * variation(),
            stable_funding=base_stable * variation(),
            required_stable_funding=base_required * variation(),
            currency_breakdown={
                "USD": base_cash * Decimal('0.65') * variation(),
                "EUR": base_cash * Decimal('0.20') * variation(),
                "GBP": base_cash * Decimal('0.10') * variation(),
                "JPY": base_cash * Decimal('0.05') * variation()
            }
        )
        
        dashboard.add_snapshot(snapshot)
    
    return dashboard


def analyze_liquidity_position(dashboard):
    """Analyze liquidity position using the dashboard."""
    logger.info("Analyzing liquidity position...")
    
    # Get latest snapshot
    latest = dashboard.get_latest_snapshot()
    if not latest:
        logger.warning("No liquidity data available")
        return
    
    # Log key metrics
    logger.info(f"Liquidity position as of {latest.date}:")
    logger.info(f"Total cash: ${latest.total_cash}")
    logger.info(f"HQLA: ${latest.high_quality_liquid_assets}")
    logger.info(f"LCR: {latest.lcr:.2f}")
    logger.info(f"NSFR: {latest.nsfr:.2f}")
    
    # Check for alerts
    alerts = dashboard.get_liquidity_alerts()
    if alerts:
        logger.warning("Liquidity alerts detected:")
        for alert in alerts:
            logger.warning(f"  - {alert}")
    else:
        logger.info("No liquidity alerts detected")
    
    # Generate charts
    output_dir = os.path.join(project_root, "treasury", "reports")
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        lcr_chart = dashboard.generate_lcr_nsfr_chart(
            output_path=os.path.join(output_dir, "liquidity_ratios.png")
        )
        cash_chart = dashboard.generate_cash_position_chart(
            output_path=os.path.join(output_dir, "cash_position.png")
        )
        currency_chart = dashboard.generate_currency_breakdown_chart(
            output_path=os.path.join(output_dir, "currency_breakdown.png")
        )
        
        dashboard.export_dashboard_data(
            os.path.join(output_dir, "dashboard_data.json"), format='json'
        )
        
        logger.info(f"Generated liquidity reports in {output_dir}")
    except Exception as e:
        logger.error(f"Error generating charts: {str(e)}")


def setup_derivatives_portfolio():
    """Set up and manage a derivatives portfolio."""
    logger.info("Setting up derivatives portfolio...")
    
    # Initialize managers for different derivative types
    options_risk_manager = DerivativesRiskManager()
    swap_manager = SwapManager()
    futures_manager = FuturesManager()
    
    # Create a comprehensive derivatives risk manager that will aggregate all positions
    derivatives_risk_manager = DerivativesRiskManager()
    
    # 1. Setup Options
    today = datetime.date.today()
    
    # Create some option contracts
    spy_call = Option(
        id="OPT_SPY_CALL",
        underlying="SPY",
        option_type=OptionType.CALL,
        style=OptionStyle.AMERICAN,
        strike_price=Decimal("450.0"),
        expiry_date=today + datetime.timedelta(days=30),
        contract_size=100,
        currency="USD"
    )
    
    qqq_put = Option(
        id="OPT_QQQ_PUT",
        underlying="QQQ",
        option_type=OptionType.PUT,
        style=OptionStyle.EUROPEAN,
        strike_price=Decimal("380.0"),
        expiry_date=today + datetime.timedelta(days=60),
        contract_size=100,
        currency="USD"
    )
    
    # Create derivative positions from options
    spy_call_position = create_option_position_from_option(
        option_id="POS_SPY_CALL",
        option=spy_call,
        quantity=10,  # Long 10 contracts
        spot_price=440.0,
        risk_free_rate=0.045,
        volatility=0.20,
        option_price=12.50,
        counterparty="Broker A"
    )
    
    qqq_put_position = create_option_position_from_option(
        option_id="POS_QQQ_PUT",
        option=qqq_put,
        quantity=-5,  # Short 5 contracts
        spot_price=390.0,
        risk_free_rate=0.045,
        volatility=0.22,
        option_price=15.75,
        counterparty="Broker B"
    )
    
    # Add option positions to the risk manager
    options_risk_manager.add_position(spy_call_position)
    options_risk_manager.add_position(qqq_put_position)
    derivatives_risk_manager.add_position(spy_call_position)
    derivatives_risk_manager.add_position(qqq_put_position)
    
    logger.info(f"Added {len(options_risk_manager.positions)} option positions")
    
    # 2. Setup Interest Rate Swaps
    # Set up yield curve for pricing
    usd_curve = {
        "0.25": 0.0425,  # 3 month
        "0.5": 0.0440,   # 6 month
        "1": 0.0455,     # 1 year
        "2": 0.0465,     # 2 year
        "3": 0.0470,     # 3 year
        "5": 0.0480,     # 5 year
        "7": 0.0485,     # 7 year
        "10": 0.0490     # 10 year
    }
    swap_manager.update_yield_curve("USD", usd_curve)
    
    # Set up reference rates
    swap_manager.update_reference_rate("SOFR", 0.0430)
    swap_manager.update_reference_rate("EURIBOR3M", 0.0350)
    
    # Create swaps
    five_year_swap = swap_manager.create_interest_rate_swap(
        id="SWAP_5Y_USD",
        effective_date=today,
        maturity_date=today.replace(year=today.year + 5),
        fixed_rate=Decimal("0.0465"),  # 4.65%
        floating_rate_index="SOFR",
        notional=Decimal("10000000"),  # 10 million
        currency="USD",
        payment_frequency=PaymentFrequency.QUARTERLY,
        day_count_convention=DayCountConvention.THIRTY_360,
        floating_spread=Decimal("0.0010"),  # 10 basis points
        pay_fixed=True,
        counterparty="Bank XYZ"
    )
    
    # Value the swap
    swap_value = swap_manager.value_swap("SWAP_5Y_USD")
    
    # Calculate risk metrics
    swap_risk = swap_manager.calculate_swap_risk("SWAP_5Y_USD")
    
    # Create a derivative position from the swap
    swap_position = create_swap_position_from_swap(
        swap_id="POS_SWAP_5Y_USD",
        swap=five_year_swap,
        market_value=swap_value.get("value", 0),
        risk_metrics={
            "dv01": swap_risk["dv01"],
            "duration": swap_risk["duration"],
            "var_95": abs(swap_value.get("value", 0) * 0.05)  # Simplified VaR calculation
        }
    )
    
    # Add swap position to the comprehensive risk manager
    derivatives_risk_manager.add_position(swap_position)
    
    logger.info(f"Added swap with notional {five_year_swap.legs[0].notional_amount:,} {five_year_swap.legs[0].currency}")
    
    # 3. Setup Futures
    # Create some futures contracts
    tn_future = FuturesContract(
        ticker="ZT",
        contract_month="MAR-24",
        futures_type=FuturesType.INTEREST_RATE,
        exchange="CBOT",
        tick_size=Decimal("0.0078125"),  # 1/128 of a point
        tick_value=Decimal("15.625"),    # Value of one tick
        contract_size=100000,            # $100,000 face value
        currency="USD",
        expiry_date=today.replace(year=today.year + 1, month=3, day=20)
    )
    
    futures_manager.add_contract(tn_future)
    
    # Create futures position
    future_position = futures_manager.create_position(
        contract_code="ZT MAR-24",
        quantity=10,  # Long 10 contracts
        entry_price=Decimal("108.25"),
        initial_margin=Decimal("5000")  # $5,000 initial margin
    )
    
    # Create derivative position from futures position
    future_derivative_position = create_future_position_from_future(
        position_id="POS_ZT_MAR24",
        future_position=future_position
    )
    
    # Add future position to the comprehensive risk manager
    derivatives_risk_manager.add_position(future_derivative_position)
    
    logger.info(f"Added futures position with {future_position.quantity} contracts")
    
    # 4. Risk Management
    # Set risk limits
    derivatives_risk_manager.set_risk_limit(
        RiskMetricType.VALUE_AT_RISK,
        Decimal("500000"),
        Decimal("0.8"),
        description="Maximum portfolio VaR"
    )
    
    derivatives_risk_manager.set_risk_limit(
        RiskMetricType.DELTA,
        Decimal("2000000"),
        Decimal("0.8"),
        description="Maximum portfolio delta exposure"
    )
    
    # Define stress scenarios
    derivatives_risk_manager.define_stress_scenario(
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
    
    derivatives_risk_manager.define_stress_scenario(
        "market_crash",
        "Severe equity market crash with volatility spike",
        {
            "equity_price": {
                "SPY": -0.20,
                "QQQ": -0.15
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
    
    # Generate a comprehensive risk report
    risk_report = derivatives_risk_manager.generate_risk_report()
    report_text = derivatives_risk_manager.format_risk_report(risk_report)
    
    logger.info("Generated derivatives risk report")
    
    # Optional: Save report to file
    try:
        output_dir = os.path.join(current_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        with open(os.path.join(output_dir, "derivatives_risk_report.txt"), "w") as f:
            f.write(report_text)
        
        logger.info(f"Risk report saved to {os.path.join(output_dir, 'derivatives_risk_report.txt')}")
    except Exception as e:
        logger.error(f"Error saving risk report: {str(e)}")
        
    return derivatives_risk_manager, risk_report


def integrate_with_risk_compliance(portfolio, dashboard, derivatives_risk_manager=None):
    """Integrate with risk-compliance module if available."""
    if not risk_compliance_available:
        logger.warning("Skipping risk-compliance integration (module not available)")
        return
    
    logger.info("Integrating with risk-compliance module...")
    
    try:
        # Add audit trail entries for bond portfolio
        audit_trail_manager.add_entry(
            action="treasury_portfolio_valuation",
            details={
                "portfolio_name": portfolio.name,
                "portfolio_value": str(sum(position.face_value_position 
                                         for position in portfolio.positions.values())),
                "number_of_positions": len(portfolio.positions)
            },
            user="system",
            source_module="treasury"
        )
        
        # Add audit trail entries for derivatives if available
        if derivatives_risk_manager:
            # Create summary of derivatives positions
            derivatives_summary = {
                "num_positions": len(derivatives_risk_manager.positions),
                "instrument_types": {},
                "total_notional": str(sum(pos.notional_value for pos in derivatives_risk_manager.positions)),
                "total_market_value": str(sum(pos.market_value for pos in derivatives_risk_manager.positions))
            }
            
            # Count positions by instrument type
            for position in derivatives_risk_manager.positions:
                if position.instrument_type in derivatives_summary["instrument_types"]:
                    derivatives_summary["instrument_types"][position.instrument_type] += 1
                else:
                    derivatives_summary["instrument_types"][position.instrument_type] = 1
            
            # Add derivatives audit entry
            audit_trail_manager.add_entry(
                action="treasury_derivatives_valuation",
                details=derivatives_summary,
                user="system",
                source_module="treasury.derivatives"
            )
            
            # Report any risk limit breaches to fraud/risk monitoring system
            if hasattr(transaction_monitor, 'report_risk_limit_breaches'):
                risk_limits = derivatives_risk_manager.get_risk_limits()
                breached_limits = []
                
                for limit_type, limit in risk_limits.items():
                    current_value = derivatives_risk_manager.calculate_risk_metric(limit_type)
                    if current_value > limit.threshold * limit.warning_level:
                        breached_limits.append({
                            "type": str(limit_type),
                            "threshold": str(limit.threshold),
                            "current_value": str(current_value),
                            "warning_level": str(limit.warning_level),
                            "description": limit.description
                        })
                
                if breached_limits:
                    transaction_monitor.report_risk_limit_breaches(
                        module="treasury.derivatives",
                        breaches=breached_limits,
                        timestamp=datetime.datetime.now().isoformat()
                    )
        
        # Generate regulatory report for liquidity
        if hasattr(regulatory_reporting_system, 'generate_liquidity_report'):
            latest = dashboard.get_latest_snapshot()
            if latest:
                report = regulatory_reporting_system.generate_liquidity_report(
                    report_date=latest.date,
                    lcr=float(latest.lcr),
                    nsfr=float(latest.nsfr),
                    hqla=float(latest.high_quality_liquid_assets),
                    short_term_obligations=float(latest.short_term_obligations),
                    currency_breakdown={k: float(v) for k, v in latest.currency_breakdown.items()}
                )
                logger.info(f"Generated regulatory report: {report['id']}")
                
                # Add derivatives risk data to regulatory reporting if available
                if derivatives_risk_manager and hasattr(regulatory_reporting_system, 'append_derivatives_data'):
                    # Get risk metrics for derivatives
                    var_95 = derivatives_risk_manager.calculate_risk_metric(RiskMetricType.VALUE_AT_RISK)
                    delta = derivatives_risk_manager.calculate_risk_metric(RiskMetricType.DELTA)
                    
                    # Add stress test results if available
                    stress_test_results = {}
                    for scenario in derivatives_risk_manager.get_stress_scenarios():
                        result = derivatives_risk_manager.run_stress_test(scenario)
                        stress_test_results[scenario] = {
                            "pnl_impact": str(result.get("pnl_impact", 0)),
                            "description": derivatives_risk_manager.get_scenario_description(scenario)
                        }
                    
                    # Append to report
                    regulatory_reporting_system.append_derivatives_data(
                        report_id=report["id"],
                        var_95=float(var_95),
                        delta_exposure=float(delta),
                        num_positions=len(derivatives_risk_manager.positions),
                        stress_test_results=stress_test_results
                    )
        
        logger.info("Risk-compliance integration complete")
    except Exception as e:
        logger.error(f"Error during risk-compliance integration: {str(e)}")


def main():
    """Main function to run the treasury integration example."""
    logger.info("Starting Treasury Integration Example")
    
    # Load configuration
    config = get_config()
    
    # Setup bond portfolio
    portfolio, bonds = setup_bond_portfolio()
    
    # Analyze portfolio
    market_prices = analyze_bond_portfolio(portfolio, bonds)
    
    # Setup liquidity dashboard
    dashboard = setup_liquidity_dashboard()
    
    # Analyze liquidity
    analyze_liquidity_position(dashboard)
    
    # Setup derivatives portfolio
    derivatives_risk_manager, risk_report = setup_derivatives_portfolio()
    
    # Integrate with risk-compliance
    integrate_with_risk_compliance(portfolio, dashboard, derivatives_risk_manager)
    
    logger.info("Treasury Integration Example completed successfully")


if __name__ == "__main__":
    main()