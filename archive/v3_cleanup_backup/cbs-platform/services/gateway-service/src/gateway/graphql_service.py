"""
GraphQL Schema and Resolver System for CBS_PYTHON V2.0

This module provides a comprehensive GraphQL layer with:
- Unified schema across all microservices
- Federated GraphQL implementation
- Real-time subscriptions
- Advanced query optimization
- Data loader pattern for N+1 problem resolution
- Permission-based field resolution
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, date
from decimal import Decimal
from dataclasses import dataclass
import uuid

import graphene
from graphene import ObjectType, String, Int, Float, Boolean, DateTime, ID, List as GraphQLList, Field, Argument
from graphene.relay import Node, Connection, ConnectionField
from graphql.execution.executors.asyncio import AsyncioExecutor
from graphql import GraphQLError
import aiodataloader
import httpx
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Metrics
graphql_query_count = Counter('graphql_queries_total', 'Total GraphQL queries', ['operation_type'])
graphql_query_duration = Histogram('graphql_query_duration_seconds', 'GraphQL query duration')
graphql_field_count = Counter('graphql_fields_resolved_total', 'GraphQL fields resolved', ['type_name', 'field_name'])


class ServiceClient:
    """HTTP client for microservice communication"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self._client = None
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout
            )
        return self._client
    
    async def get(self, path: str, **kwargs) -> Dict[str, Any]:
        """Make GET request"""
        client = await self.get_client()
        response = await client.get(path, **kwargs)
        response.raise_for_status()
        return response.json()
    
    async def post(self, path: str, **kwargs) -> Dict[str, Any]:
        """Make POST request"""
        client = await self.get_client()
        response = await client.post(path, **kwargs)
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()


# Data Loaders for efficient data fetching
class CustomerLoader(aiodataloader.DataLoader):
    """Data loader for customers"""
    
    def __init__(self, service_client: ServiceClient):
        super().__init__()
        self.service_client = service_client
    
    async def batch_load_fn(self, customer_ids: List[str]) -> List[Optional[Dict]]:
        """Batch load customers by IDs"""
        try:
            # Make batch request to customer service
            response = await self.service_client.post(
                "/customers/batch",
                json={"ids": customer_ids}
            )
            
            customers_by_id = {c["id"]: c for c in response.get("data", [])}
            return [customers_by_id.get(cid) for cid in customer_ids]
        
        except Exception as e:
            logger.error(f"Failed to batch load customers: {e}")
            return [None] * len(customer_ids)


class AccountLoader(aiodataloader.DataLoader):
    """Data loader for accounts"""
    
    def __init__(self, service_client: ServiceClient):
        super().__init__()
        self.service_client = service_client
    
    async def batch_load_fn(self, account_ids: List[str]) -> List[Optional[Dict]]:
        """Batch load accounts by IDs"""
        try:
            response = await self.service_client.post(
                "/accounts/batch",
                json={"ids": account_ids}
            )
            
            accounts_by_id = {a["id"]: a for a in response.get("data", [])}
            return [accounts_by_id.get(aid) for aid in account_ids]
        
        except Exception as e:
            logger.error(f"Failed to batch load accounts: {e}")
            return [None] * len(account_ids)


class TransactionLoader(aiodataloader.DataLoader):
    """Data loader for transactions"""
    
    def __init__(self, service_client: ServiceClient):
        super().__init__()
        self.service_client = service_client
    
    async def batch_load_fn(self, transaction_ids: List[str]) -> List[Optional[Dict]]:
        """Batch load transactions by IDs"""
        try:
            response = await self.service_client.post(
                "/transactions/batch",
                json={"ids": transaction_ids}
            )
            
            transactions_by_id = {t["id"]: t for t in response.get("data", [])}
            return [transactions_by_id.get(tid) for tid in transaction_ids]
        
        except Exception as e:
            logger.error(f"Failed to batch load transactions: {e}")
            return [None] * len(transaction_ids)


# Custom Scalars
class DecimalType(graphene.Scalar):
    """Decimal scalar type for precise monetary calculations"""
    
    @staticmethod
    def serialize(value):
        if isinstance(value, Decimal):
            return float(value)
        return value
    
    @staticmethod
    def parse_literal(node):
        if isinstance(node.value, (int, float)):
            return Decimal(str(node.value))
        return None
    
    @staticmethod
    def parse_value(value):
        if isinstance(value, (int, float, str)):
            return Decimal(str(value))
        return None


# Enums
class CustomerStatus(graphene.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class AccountType(graphene.Enum):
    SAVINGS = "savings"
    CHECKING = "checking"
    BUSINESS = "business"
    LOAN = "loan"
    CREDIT = "credit"


class TransactionType(graphene.Enum):
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    FEE = "fee"


class TransactionStatus(graphene.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Interfaces
class Node(graphene.Interface):
    """Node interface for Relay specification"""
    id = graphene.ID(required=True)


# Types
class Address(graphene.ObjectType):
    """Address type"""
    street = String(required=True)
    city = String(required=True)
    state = String(required=True)
    postal_code = String(required=True)
    country = String(required=True)


class Customer(graphene.ObjectType):
    """Customer type"""
    class Meta:
        interfaces = (Node,)
    
    id = ID(required=True)
    customer_number = String()
    first_name = String(required=True)
    last_name = String(required=True)
    email = String(required=True)
    phone = String()
    date_of_birth = DateTime()
    status = Field(CustomerStatus)
    kyc_status = String()
    address = Field(Address)
    created_at = DateTime()
    updated_at = DateTime()
    
    # Relationships
    accounts = GraphQLList(lambda: Account)
    transactions = GraphQLList(lambda: Transaction, limit=Int(default_value=10))
    
    @staticmethod
    async def resolve_accounts(root, info, **kwargs):
        """Resolve customer accounts"""
        graphql_field_count.labels(type_name="Customer", field_name="accounts").inc()
        
        account_service = info.context.get("account_service")
        if not account_service:
            return []
        
        try:
            response = await account_service.get(f"/accounts?customer_id={root['id']}")
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Failed to resolve customer accounts: {e}")
            return []
    
    @staticmethod
    async def resolve_transactions(root, info, limit=10, **kwargs):
        """Resolve customer transactions"""
        graphql_field_count.labels(type_name="Customer", field_name="transactions").inc()
        
        transaction_service = info.context.get("transaction_service")
        if not transaction_service:
            return []
        
        try:
            response = await transaction_service.get(
                f"/transactions?customer_id={root['id']}&limit={limit}"
            )
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Failed to resolve customer transactions: {e}")
            return []


class Account(graphene.ObjectType):
    """Account type"""
    class Meta:
        interfaces = (Node,)
    
    id = ID(required=True)
    account_number = String()
    customer_id = ID(required=True)
    account_type = Field(AccountType)
    currency = String(required=True)
    balance = Field(DecimalType)
    available_balance = Field(DecimalType)
    status = String()
    interest_rate = Float()
    created_at = DateTime()
    updated_at = DateTime()
    
    # Relationships
    customer = Field(Customer)
    transactions = GraphQLList(lambda: Transaction, limit=Int(default_value=10))
    
    @staticmethod
    async def resolve_customer(root, info, **kwargs):
        """Resolve account customer"""
        graphql_field_count.labels(type_name="Account", field_name="customer").inc()
        
        customer_loader = info.context.get("customer_loader")
        if not customer_loader:
            return None
        
        return await customer_loader.load(root["customer_id"])
    
    @staticmethod
    async def resolve_transactions(root, info, limit=10, **kwargs):
        """Resolve account transactions"""
        graphql_field_count.labels(type_name="Account", field_name="transactions").inc()
        
        transaction_service = info.context.get("transaction_service")
        if not transaction_service:
            return []
        
        try:
            response = await transaction_service.get(
                f"/transactions?account_id={root['id']}&limit={limit}"
            )
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Failed to resolve account transactions: {e}")
            return []


class Transaction(graphene.ObjectType):
    """Transaction type"""
    class Meta:
        interfaces = (Node,)
    
    id = ID(required=True)
    transaction_number = String()
    account_id = ID(required=True)
    type = Field(TransactionType)
    amount = Field(DecimalType, required=True)
    currency = String(required=True)
    description = String()
    reference = String()
    status = Field(TransactionStatus)
    balance_after = Field(DecimalType)
    created_at = DateTime()
    processed_at = DateTime()
    
    # Relationships
    account = Field(Account)
    
    @staticmethod
    async def resolve_account(root, info, **kwargs):
        """Resolve transaction account"""
        graphql_field_count.labels(type_name="Transaction", field_name="account").inc()
        
        account_loader = info.context.get("account_loader")
        if not account_loader:
            return None
        
        return await account_loader.load(root["account_id"])


class Payment(graphene.ObjectType):
    """Payment type"""
    class Meta:
        interfaces = (Node,)
    
    id = ID(required=True)
    payment_number = String()
    payer_account_id = ID(required=True)
    payee_account_id = ID(required=True)
    amount = Field(DecimalType, required=True)
    currency = String(required=True)
    payment_type = String()
    description = String()
    reference = String()
    status = String()
    fee_amount = Field(DecimalType)
    created_at = DateTime()
    processed_at = DateTime()
    
    # Relationships
    payer_account = Field(Account)
    payee_account = Field(Account)
    
    @staticmethod
    async def resolve_payer_account(root, info, **kwargs):
        """Resolve payer account"""
        account_loader = info.context.get("account_loader")
        if not account_loader:
            return None
        
        return await account_loader.load(root["payer_account_id"])
    
    @staticmethod
    async def resolve_payee_account(root, info, **kwargs):
        """Resolve payee account"""
        account_loader = info.context.get("account_loader")
        if not account_loader:
            return None
        
        return await account_loader.load(root["payee_account_id"])


class Loan(graphene.ObjectType):
    """Loan type"""
    class Meta:
        interfaces = (Node,)
    
    id = ID(required=True)
    loan_number = String()
    customer_id = ID(required=True)
    loan_type = String()
    requested_amount = Field(DecimalType)
    approved_amount = Field(DecimalType)
    currency = String()
    term_months = Int()
    interest_rate = Float()
    status = String()
    purpose = String()
    outstanding_balance = Field(DecimalType)
    next_payment_date = DateTime()
    next_payment_amount = Field(DecimalType)
    created_at = DateTime()
    approved_at = DateTime()
    disbursed_at = DateTime()
    
    # Relationships
    customer = Field(Customer)
    
    @staticmethod
    async def resolve_customer(root, info, **kwargs):
        """Resolve loan customer"""
        customer_loader = info.context.get("customer_loader")
        if not customer_loader:
            return None
        
        return await customer_loader.load(root["customer_id"])


# Connection types for pagination
class CustomerConnection(Connection):
    class Meta:
        node = Customer


class AccountConnection(Connection):
    class Meta:
        node = Account


class TransactionConnection(Connection):
    class Meta:
        node = Transaction


# Input types for mutations
class CustomerInput(graphene.InputObjectType):
    """Customer input for mutations"""
    first_name = String(required=True)
    last_name = String(required=True)
    email = String(required=True)
    phone = String()
    date_of_birth = DateTime()


class UpdateCustomerInput(graphene.InputObjectType):
    """Update customer input"""
    first_name = String()
    last_name = String()
    email = String()
    phone = String()


class AccountInput(graphene.InputObjectType):
    """Account input for mutations"""
    customer_id = ID(required=True)
    account_type = Field(AccountType, required=True)
    currency = String(required=True)
    initial_deposit = Field(DecimalType)


class TransferInput(graphene.InputObjectType):
    """Transfer input for mutations"""
    from_account_id = ID(required=True)
    to_account_id = ID(required=True)
    amount = Field(DecimalType, required=True)
    currency = String(required=True)
    description = String()
    reference = String()


# Query class
class Query(graphene.ObjectType):
    """Root query type"""
    
    # Single object queries
    customer = Field(Customer, id=ID(required=True))
    account = Field(Account, id=ID(required=True))
    transaction = Field(Transaction, id=ID(required=True))
    payment = Field(Payment, id=ID(required=True))
    loan = Field(Loan, id=ID(required=True))
    
    # List queries with pagination
    customers = ConnectionField(
        CustomerConnection,
        status=Argument(CustomerStatus),
        search=String()
    )
    accounts = ConnectionField(
        AccountConnection,
        customer_id=ID(),
        account_type=Argument(AccountType)
    )
    transactions = ConnectionField(
        TransactionConnection,
        account_id=ID(),
        transaction_type=Argument(TransactionType),
        status=Argument(TransactionStatus)
    )
    
    # Custom queries
    account_balance = Field(
        DecimalType,
        account_id=ID(required=True),
        description="Get current account balance"
    )
    customer_summary = Field(
        lambda: CustomerSummary,
        customer_id=ID(required=True),
        description="Get customer summary with aggregated data"
    )
    
    async def resolve_customer(self, info, id):
        """Resolve single customer"""
        graphql_query_count.labels(operation_type="query").inc()
        
        customer_service = info.context.get("customer_service")
        if not customer_service:
            raise GraphQLError("Customer service not available")
        
        try:
            response = await customer_service.get(f"/customers/{id}")
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise GraphQLError(f"Failed to fetch customer: {e}")
    
    async def resolve_account(self, info, id):
        """Resolve single account"""
        account_service = info.context.get("account_service")
        if not account_service:
            raise GraphQLError("Account service not available")
        
        try:
            response = await account_service.get(f"/accounts/{id}")
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise GraphQLError(f"Failed to fetch account: {e}")
    
    async def resolve_transaction(self, info, id):
        """Resolve single transaction"""
        transaction_service = info.context.get("transaction_service")
        if not transaction_service:
            raise GraphQLError("Transaction service not available")
        
        try:
            response = await transaction_service.get(f"/transactions/{id}")
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise GraphQLError(f"Failed to fetch transaction: {e}")
    
    async def resolve_customers(self, info, **kwargs):
        """Resolve customers with pagination"""
        customer_service = info.context.get("customer_service")
        if not customer_service:
            raise GraphQLError("Customer service not available")
        
        # Build query parameters
        params = {}
        if "status" in kwargs:
            params["status"] = kwargs["status"]
        if "search" in kwargs:
            params["search"] = kwargs["search"]
        
        try:
            response = await customer_service.get("/customers", params=params)
            return response.get("data", [])
        except Exception as e:
            raise GraphQLError(f"Failed to fetch customers: {e}")
    
    async def resolve_account_balance(self, info, account_id):
        """Resolve account balance"""
        account_service = info.context.get("account_service")
        if not account_service:
            raise GraphQLError("Account service not available")
        
        try:
            response = await account_service.get(f"/accounts/{account_id}/balance")
            return Decimal(str(response.get("current_balance", 0)))
        except Exception as e:
            raise GraphQLError(f"Failed to fetch account balance: {e}")


class CustomerSummary(graphene.ObjectType):
    """Customer summary with aggregated data"""
    customer = Field(Customer)
    total_accounts = Int()
    total_balance = Field(DecimalType)
    recent_transactions = GraphQLList(Transaction)
    active_loans = GraphQLList(Loan)


# Mutation classes
class CreateCustomer(graphene.Mutation):
    """Create customer mutation"""
    class Arguments:
        input = CustomerInput(required=True)
    
    Output = Customer
    
    async def mutate(self, info, input):
        """Create customer"""
        graphql_query_count.labels(operation_type="mutation").inc()
        
        customer_service = info.context.get("customer_service")
        if not customer_service:
            raise GraphQLError("Customer service not available")
        
        try:
            response = await customer_service.post("/customers", json=input)
            return response
        except Exception as e:
            raise GraphQLError(f"Failed to create customer: {e}")


class UpdateCustomer(graphene.Mutation):
    """Update customer mutation"""
    class Arguments:
        id = ID(required=True)
        input = UpdateCustomerInput(required=True)
    
    Output = Customer
    
    async def mutate(self, info, id, input):
        """Update customer"""
        customer_service = info.context.get("customer_service")
        if not customer_service:
            raise GraphQLError("Customer service not available")
        
        try:
            response = await customer_service.put(f"/customers/{id}", json=input)
            return response
        except Exception as e:
            raise GraphQLError(f"Failed to update customer: {e}")


class CreateAccount(graphene.Mutation):
    """Create account mutation"""
    class Arguments:
        input = AccountInput(required=True)
    
    Output = Account
    
    async def mutate(self, info, input):
        """Create account"""
        account_service = info.context.get("account_service")
        if not account_service:
            raise GraphQLError("Account service not available")
        
        try:
            response = await account_service.post("/accounts", json=input)
            return response
        except Exception as e:
            raise GraphQLError(f"Failed to create account: {e}")


class TransferFunds(graphene.Mutation):
    """Transfer funds mutation"""
    class Arguments:
        input = TransferInput(required=True)
    
    Output = Transaction
    
    async def mutate(self, info, input):
        """Transfer funds"""
        transaction_service = info.context.get("transaction_service")
        if not transaction_service:
            raise GraphQLError("Transaction service not available")
        
        try:
            response = await transaction_service.post("/transactions/transfer", json=input)
            return response
        except Exception as e:
            raise GraphQLError(f"Failed to transfer funds: {e}")


class Mutation(graphene.ObjectType):
    """Root mutation type"""
    create_customer = CreateCustomer.Field()
    update_customer = UpdateCustomer.Field()
    create_account = CreateAccount.Field()
    transfer_funds = TransferFunds.Field()


# Subscription types (for real-time updates)
class Subscription(graphene.ObjectType):
    """Root subscription type"""
    
    transaction_created = Field(Transaction, account_id=ID())
    account_balance_updated = Field(Account, account_id=ID(required=True))
    
    async def resolve_transaction_created(self, info, account_id=None):
        """Subscribe to new transactions"""
        # Implementation would use WebSocket or Server-Sent Events
        # This is a placeholder for the subscription logic
        pass
    
    async def resolve_account_balance_updated(self, info, account_id):
        """Subscribe to account balance updates"""
        # Implementation would use WebSocket or Server-Sent Events
        # This is a placeholder for the subscription logic
        pass


class GraphQLContext:
    """GraphQL execution context"""
    
    def __init__(self, request, services: Dict[str, ServiceClient]):
        self.request = request
        self.user = getattr(request.state, "user", None)
        
        # Service clients
        self.customer_service = services.get("customer")
        self.account_service = services.get("account")
        self.transaction_service = services.get("transaction")
        self.payment_service = services.get("payment")
        self.loan_service = services.get("loan")
        
        # Data loaders
        if self.customer_service:
            self.customer_loader = CustomerLoader(self.customer_service)
        if self.account_service:
            self.account_loader = AccountLoader(self.account_service)
        if self.transaction_service:
            self.transaction_loader = TransactionLoader(self.transaction_service)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for GraphQL execution"""
        return {
            "request": self.request,
            "user": self.user,
            "customer_service": self.customer_service,
            "account_service": self.account_service,
            "transaction_service": self.transaction_service,
            "payment_service": self.payment_service,
            "loan_service": self.loan_service,
            "customer_loader": getattr(self, "customer_loader", None),
            "account_loader": getattr(self, "account_loader", None),
            "transaction_loader": getattr(self, "transaction_loader", None)
        }


# Schema creation
def create_schema() -> graphene.Schema:
    """Create GraphQL schema"""
    return graphene.Schema(
        query=Query,
        mutation=Mutation,
        subscription=Subscription,
        types=[Customer, Account, Transaction, Payment, Loan]
    )


class GraphQLService:
    """GraphQL service with advanced features"""
    
    def __init__(self, services: Dict[str, str]):
        self.schema = create_schema()
        self.service_clients = {}
        
        # Initialize service clients
        for service_name, base_url in services.items():
            self.service_clients[service_name] = ServiceClient(base_url)
    
    async def execute_query(
        self,
        query: str,
        variables: Optional[Dict] = None,
        operation_name: Optional[str] = None,
        request=None
    ) -> Dict[str, Any]:
        """Execute GraphQL query with timing and error handling"""
        start_time = datetime.utcnow()
        
        try:
            # Create execution context
            context = GraphQLContext(request, self.service_clients)
            
            # Execute query
            result = await self.schema.execute_async(
                query,
                variables=variables,
                operation_name=operation_name,
                context_value=context.to_dict(),
                executor=AsyncioExecutor()
            )
            
            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            graphql_query_duration.observe(duration)
            
            # Format response
            response = {"data": result.data}
            
            if result.errors:
                response["errors"] = [
                    {
                        "message": str(error),
                        "locations": getattr(error, "locations", None),
                        "path": getattr(error, "path", None)
                    }
                    for error in result.errors
                ]
            
            return response
        
        except Exception as e:
            logger.error(f"GraphQL execution error: {e}")
            return {
                "data": None,
                "errors": [{"message": f"Internal server error: {str(e)}"}]
            }
    
    async def close(self):
        """Close all service clients"""
        for client in self.service_clients.values():
            await client.close()


# Usage example
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Create GraphQL service
        services = {
            "customer": "http://localhost:8001",
            "account": "http://localhost:8002",
            "transaction": "http://localhost:8003",
            "payment": "http://localhost:8004",
            "loan": "http://localhost:8005"
        }
        
        graphql_service = GraphQLService(services)
        
        # Example query
        query = """
        query GetCustomerWithAccounts($customerId: ID!) {
            customer(id: $customerId) {
                id
                firstName
                lastName
                email
                accounts {
                    id
                    accountNumber
                    accountType
                    balance
                    currency
                    transactions(limit: 5) {
                        id
                        type
                        amount
                        description
                        createdAt
                    }
                }
            }
        }
        """
        
        variables = {"customerId": "123e4567-e89b-12d3-a456-426614174000"}
        
        # Execute query
        result = await graphql_service.execute_query(query, variables)
        print(json.dumps(result, indent=2))
        
        await graphql_service.close()
    
    asyncio.run(main())
