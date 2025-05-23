# Treasury Clean Architecture Guide

Last Updated: May 23, 2025

## Overview

This document provides guidance for implementing and maintaining Clean Architecture in the Treasury module of the CBS_PYTHON system. The Treasury module manages liquidity, investments, forex operations, bonds, derivatives, and risk management for the bank's financial assets.

## Module-Specific Architecture

### Domain Layer Components

- **Entities**:
  - Investment: Core investment entity with valuation rules
  - LiquidityPosition: Liquidity management entity
  - Bond: Bond instrument with yield calculations
  - ForeignExchangeRate: FX rate entity with conversion rules
  - TreasuryLimit: Limit entity for treasury operations
  - Derivative: Derivative financial instrument

- **Value Objects**:
  - Money: Immutable currency and amount representation
  - InterestRate: Immutable interest rate with calculation rules
  - ExchangeRate: Immutable FX rate representation
  - YieldCurve: Immutable yield curve representation
  - RiskRating: Classification of investment risk
  - Duration: Time-based value representation for investments
  - MaturityDate: Time representation for investment maturity

- **Domain Services**:
  - InvestmentValuationService: Investment valuation calculations
  - LiquidityManagementService: Liquidity analysis and forecasting
  - ForeignExchangeService: FX conversion and risk assessment
  - BondPricingService: Bond pricing calculations
  - YieldCalculationService: Yield analysis for investments
  - RiskAssessmentService: Risk evaluation for treasury operations

- **Repository Interfaces**:
  - IInvestmentRepository: Interface for investment data access
  - ILiquidityRepository: Interface for liquidity position data
  - IBondRepository: Interface for bond instrument data
  - IForexRepository: Interface for foreign exchange data
  - IDerivativeRepository: Interface for derivative instrument data
  - ITreasuryLimitRepository: Interface for treasury limits
  - IMarketDataRepository: Interface for market data access

### Application Layer Components

- **Use Cases**:
  - ManageInvestmentUseCase: Handle investment operations
  - MonitorLiquidityUseCase: Track and manage liquidity
  - ExecuteForexTradeUseCase: Process FX transactions
  - ManageBondPortfolioUseCase: Handle bond operations
  - TradeDerivativeUseCase: Process derivative trades
  - EnforceTreasuryLimitsUseCase: Monitor and enforce limits
  - GenerateTreasuryReportUseCase: Create treasury reports
  - ForecastLiquidityUseCase: Predict liquidity positions
  - CalculateInvestmentReturnsUseCase: Determine investment performance

- **Service Interfaces**:
  - IMarketDataService: Interface for market data retrieval
  - IRiskManagementService: Interface for risk analysis
  - IReportingService: Interface for treasury reporting
  - IComplianceCheckService: Interface for regulatory compliance
  - ILimitMonitoringService: Interface for limit enforcement
  - ITradingPlatformService: Interface for external trading platforms

### Infrastructure Layer Components

- **Repositories**:
  - InvestmentRepository: Implementation of IInvestmentRepository
  - LiquidityRepository: Implementation of ILiquidityRepository
  - BondRepository: Implementation of IBondRepository
  - ForexRepository: Implementation of IForexRepository
  - DerivativeRepository: Implementation of IDerivativeRepository
  - TreasuryLimitRepository: Implementation of ITreasuryLimitRepository
  - MarketDataRepository: Implementation of IMarketDataRepository

- **External Service Adapters**:
  - MarketDataAdapter: Implementation for market data retrieval
  - RiskManagementAdapter: Implementation for risk analysis
  - ReportingAdapter: Implementation for treasury reporting
  - ComplianceAdapter: Implementation for regulatory compliance
  - TradingPlatformAdapter: Implementation for trading platform integration

- **Database Models**:
  - InvestmentModel: Database model for investments
  - LiquidityPositionModel: Database model for liquidity positions
  - BondModel: Database model for bonds
  - ForexRateModel: Database model for FX rates
  - DerivativeModel: Database model for derivatives
  - TreasuryLimitModel: Database model for treasury limits
  - MarketDataModel: Database model for market data
  - TreasuryTransactionModel: Database model for treasury transactions

### Presentation Layer Components

- **API Controllers**:
  - InvestmentController: REST endpoints for investment management
  - LiquidityController: REST endpoints for liquidity management
  - ForexController: REST endpoints for foreign exchange operations
  - BondController: REST endpoints for bond operations
  - DerivativeController: REST endpoints for derivative operations
  - LimitController: REST endpoints for treasury limits
  - ReportController: REST endpoints for treasury reports

- **DTOs**:
  - InvestmentDTO: Data transfer object for investments
  - LiquidityPositionDTO: Data transfer object for liquidity positions
  - BondDTO: Data transfer object for bonds
  - ForexRateDTO: Data transfer object for FX rates
  - DerivativeDTO: Data transfer object for derivatives
  - TreasuryLimitDTO: Data transfer object for treasury limits
  - TreasuryReportDTO: Data transfer object for treasury reports

## Module-Specific Guidelines

### Domain Model Guidelines

- All financial calculations must be performed in the domain layer
- Money values must use the Money value object to prevent floating-point errors
- Risk ratings must follow defined classification standards
- All treasury operations must respect defined limits
- Implement proper validation for financial instrument parameters
- Investment entities must include proper valuation methods
- FX rates must handle currency pair conversions correctly
- Bond pricing must account for yield curve changes

### Use Case Implementation

- All treasury operations must include risk assessment
- Implement proper error handling for market data unavailability
- Include comprehensive audit logging for all treasury transactions
- Enforce treasury limits during operation execution
- Implement transaction rollback for failed operations
- Market data must be validated for freshness and accuracy
- Investment performance calculations must use standard methods
- Liquidity forecasts must account for upcoming obligations

### Repository Implementation

- Use database transactions for multi-step operations
- Implement caching for frequently accessed market data
- Store historical data for rate trends and analysis
- Implement efficient querying for position summaries
- Ensure proper error handling for external data sources
- Implement versioning for investment valuations
- Use appropriate indexing for time-series treasury data

### API Design

- Follow RESTful principles for treasury endpoints
- Implement proper authentication for all financial operations
- Include comprehensive validation for all financial inputs
- Provide detailed error responses with appropriate status codes
- Use proper pagination for large dataset queries
- Include rate limiting for market data endpoints
- Support batch operations for portfolio management

## Module-Specific Version Control

### Branching

- Feature branches should be named: `feature/treasury-[feature-name]`
- Bug fixes should be named: `fix/treasury-[issue-description]`

### Commit Messages

- Include the module prefix in commit messages: `[TREASURY] feat: add bond pricing algorithm`
- Reference issue numbers when applicable: `[TREASURY] fix: resolve FX rate calculation issue (#123)`

## Related Resources

- [Central Clean Architecture Guide](../Documentation/architecture/CLEAN_ARCHITECTURE_CENTRAL_GUIDE.md)
- [Treasury Progress Tracking](./CLEAN_ARCHITECTURE_PROGRESS.md)
- [Bonds Documentation](./bonds/README.md)
- [Forex Documentation](./forex/README.md)
- [Derivatives Documentation](./derivatives/README.md)
- [Liquidity Management Documentation](./liquidity_management/README.md)
  - [ValueObject2]: [Description]

- **Domain Services**:
  - [DomainService1]: [Description]
  - [DomainService2]: [Description]

- **Repository Interfaces**:
  - [RepositoryInterface1]: [Description]
  - [RepositoryInterface2]: [Description]

### Application Layer Components

- **Use Cases**:
  - [UseCase1]: [Description]
  - [UseCase2]: [Description]
  - [UseCase3]: [Description]

- **Service Interfaces**:
  - [ServiceInterface1]: [Description]
  - [ServiceInterface2]: [Description]

### Infrastructure Layer Components

- **Repositories**:
  - [Repository1]: [Description]
  - [Repository2]: [Description]

- **External Service Adapters**:
  - [Adapter1]: [Description]
  - [Adapter2]: [Description]

- **Database Models**:
  - [Model1]: [Description]
  - [Model2]: [Description]

### Presentation Layer Components

- **API Controllers**:
  - [Controller1]: [Description]
  - [Controller2]: [Description]

- **DTOs**:
  - [DTO1]: [Description]
  - [DTO2]: [Description]

## Module-Specific Guidelines

### Domain Model Guidelines

- Implement risk calculations based on Basel standards
- Support multi-currency operations natively
- Maintain real-time position tracking

### Use Case Implementation

- [Implementation Guideline 1]
- [Implementation Guideline 2]
- [Implementation Guideline 3]

### Repository Implementation

- [Implementation Guideline 1]
- [Implementation Guideline 2]
- [Implementation Guideline 3]

### API Design

- [API Guideline 1]
- [API Guideline 2]
- [API Guideline 3]

## Module-Specific Version Control

### Branching

- Feature branches should be named: `feature/Treasury-[feature-name]`
- Bug fixes should be named: `fix/Treasury-[issue-description]`

### Commit Messages

- Include the module prefix in commit messages: `Treasury feat: add new feature`
- Reference issue numbers when applicable: `Treasury fix: resolve login issue (#123)`

### Review Process

1. [Module-specific review step 1]
2. [Module-specific review step 2]
3. [Module-specific review step 3]

## Testing Requirements

- [Testing requirement 1]
- [Testing requirement 2]
- [Testing requirement 3]

## Dependency Management

- [Dependency guideline 1]
- [Dependency guideline 2]
- [Dependency guideline 3]

## Related Resources

- [Clean Architecture Central Guide](../../Documentation/architecture/CLEAN_ARCHITECTURE_CENTRAL_GUIDE.md)
- [System Architecture](../../Documentation/architecture/SYSTEM_ARCHITECTURE.md)
- [Treasury API Documentation](./docs/API.md)
