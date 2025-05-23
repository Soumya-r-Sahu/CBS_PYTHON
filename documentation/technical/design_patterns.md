# CBS_PYTHON Design Patterns Implementation

## Introduction

This document outlines the design patterns implemented in the CBS_PYTHON codebase to promote code reuse, maintainability, and adherence to best practices. These patterns provide standardized solutions to common design problems and help create a more flexible, modular architecture.

## Implemented Design Patterns

The implementation can be found in `utils/common/design_patterns.py` and includes the following categories of design patterns:

### 1. Creational Patterns

#### Singleton Pattern

The Singleton pattern ensures that a class has only one instance and provides a global point of access to it. We provide two implementations:

```python
# Using a decorator
def singleton(cls):
    """Singleton pattern implementation as a decorator."""
    instances = {}
    
    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
        
    return get_instance
    
# Using a metaclass
class SingletonMeta(type):
    """Metaclass implementation of the Singleton pattern."""
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
```

**Usage Example**:

```python
# Using decorator
@singleton
class ConfigService:
    def __init__(self):
        self.config = self._load_config()
        
    def _load_config(self):
        # Implementation
        pass

# Using metaclass
class Logger(metaclass=SingletonMeta):
    def __init__(self):
        self.log_file = self._setup_log_file()
```

#### Factory Pattern

The Factory pattern provides an interface for creating objects without specifying the exact class of object that will be created.

```python
class Factory:
    """Factory pattern implementation."""
    
    def __init__(self):
        self._creators = {}
        
    def register(self, key, creator):
        """Register a creator function or class with a key."""
        self._creators[key] = creator
        
    def unregister(self, key):
        """Unregister a creator."""
        if key in self._creators:
            del self._creators[key]
            
    def create(self, key, *args, **kwargs):
        """Create an instance using the registered creator."""
        creator = self._creators.get(key)
        if not creator:
            raise ValueError(f"No creator registered for key: {key}")
            
        return creator(*args, **kwargs)
```

**Usage Example**:

```python
# Create a factory for payment processors
payment_factory = Factory()
payment_factory.register("card", CardPaymentProcessor)
payment_factory.register("upi", UpiPaymentProcessor)
payment_factory.register("netbanking", NetbankingPaymentProcessor)

# Create a specific processor based on payment method
processor = payment_factory.create(payment_method)
result = processor.process_payment(amount, account)
```

#### Builder Pattern

The Builder pattern separates the construction of a complex object from its representation, allowing the same construction process to create different representations.

```python
class Builder:
    """Abstract Builder base class."""
    
    def reset(self):
        """Reset the builder to its initial state."""
        raise NotImplementedError
        
    def build(self):
        """Return the built object."""
        raise NotImplementedError

class ReportBuilder(Builder):
    """Builder for complex report objects."""
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        self._report = Report()
        
    def set_title(self, title):
        self._report.title = title
        return self
        
    def add_section(self, title, content):
        self._report.add_section(title, content)
        return self
        
    def set_date_range(self, start_date, end_date):
        self._report.start_date = start_date
        self._report.end_date = end_date
        return self
        
    def set_format(self, format_type):
        self._report.format = format_type
        return self
        
    def build(self):
        report = self._report
        self.reset()
        return report
```

**Usage Example**:

```python
# Build a transaction report
builder = ReportBuilder()
report = (builder
    .set_title("Monthly Transaction Report")
    .set_date_range(start_date, end_date)
    .add_section("Summary", summary_data)
    .add_section("Transactions", transaction_data)
    .set_format("PDF")
    .build())

# Generate the report
report.generate()
```

### 2. Structural Patterns

#### Adapter Pattern

The Adapter pattern allows objects with incompatible interfaces to collaborate by wrapping an object in an adapter that conforms to the expected interface.

```python
class Target:
    """The interface the client expects to work with."""
    
    def request(self):
        raise NotImplementedError

class Adaptee:
    """The incompatible interface that needs adapting."""
    
    def specific_request(self):
        return "Specific request implementation"

class Adapter(Target):
    """Adapter that makes Adaptee compatible with Target."""
    
    def __init__(self, adaptee):
        self._adaptee = adaptee
        
    def request(self):
        # Adapt the specific request to the target interface
        return f"Adapted: {self._adaptee.specific_request()}"
```

**Usage Example**:

```python
# Adapting a legacy validation function to the new validator interface
class LegacyValidatorAdapter(Validator):
    def __init__(self, legacy_validator_func, *args):
        self.legacy_validator_func = legacy_validator_func
        self.args = args
        
    def validate(self, value):
        # Call the legacy validation function
        is_valid, error_message = self.legacy_validator_func(value, *self.args)
        return is_valid, error_message
        
# Usage
amount_validator = LegacyValidatorAdapter(legacy_validate_amount, 0.01, 100000.0)
is_valid, error = amount_validator.validate(payment.amount)
```

#### Proxy Pattern

The Proxy pattern provides a surrogate or placeholder for another object to control access to it.

```python
class Subject:
    """Interface for RealSubject and Proxy."""
    
    def request(self):
        raise NotImplementedError

class RealSubject(Subject):
    """Real object that the proxy represents."""
    
    def request(self):
        return "RealSubject: Handling request"

class Proxy(Subject):
    """Proxy controlling access to the RealSubject."""
    
    def __init__(self):
        self._real_subject = None
        
    def request(self):
        # Lazy initialization: Create the real subject only when needed
        if self._real_subject is None:
            self._real_subject = RealSubject()
        
        # Additional behaviors before forwarding the request
        print("Proxy: Logging before request")
        
        # Forward the request to the real subject
        result = self._real_subject.request()
        
        # Additional behaviors after forwarding the request
        print("Proxy: Logging after request")
        
        return result
```

**Usage Example**:

```python
# Using a proxy for database access with connection pooling
class DatabaseProxy(DatabaseInterface):
    def __init__(self):
        self._database = None
        self._connection_count = 0
        
    def connect(self):
        if self._database is None:
            self._database = RealDatabase()
        self._connection_count += 1
        return self._database.connect()
        
    def execute_query(self, query):
        # Log the query for performance monitoring
        start_time = time.time()
        result = self._database.execute_query(query)
        duration = time.time() - start_time
        
        # Log slow queries
        if duration > 1.0:
            logger.warning(f"Slow query detected: {query[:100]}... ({duration:.2f}s)")
            
        return result
```

#### Composite Pattern

The Composite pattern lets you compose objects into tree structures and then work with these structures as if they were individual objects.

```python
class Component:
    """Base Component class for both Leaf and Composite."""
    
    def operation(self):
        raise NotImplementedError
        
    def add(self, component):
        raise NotImplementedError
        
    def remove(self, component):
        raise NotImplementedError
        
    def is_composite(self):
        return False

class Leaf(Component):
    """Leaf represents end objects of a composition."""
    
    def operation(self):
        return "Leaf operation"

class Composite(Component):
    """Composite contains other components."""
    
    def __init__(self):
        self._children = []
        
    def add(self, component):
        self._children.append(component)
        
    def remove(self, component):
        self._children.remove(component)
        
    def operation(self):
        results = []
        for child in self._children:
            results.append(child.operation())
        return f"Composite [{', '.join(results)}]"
        
    def is_composite(self):
        return True
```

**Usage Example**:

```python
# Building a menu system with nested components
class MenuItem(Component):
    def __init__(self, name, action):
        self.name = name
        self.action = action
        
    def operation(self):
        return self.action()

class Menu(Composite):
    def __init__(self, name):
        super().__init__()
        self.name = name
        
    def display(self):
        print(f"Menu: {self.name}")
        for i, child in enumerate(self._children):
            prefix = "--" if child.is_composite() else "  "
            print(f"{i+1}. {prefix} {child.name}")

# Usage
main_menu = Menu("Main Menu")
file_menu = Menu("File")
main_menu.add(file_menu)

file_menu.add(MenuItem("Open", open_action))
file_menu.add(MenuItem("Save", save_action))

main_menu.display()
```

### 3. Behavioral Patterns

#### Observer Pattern

The Observer pattern defines a one-to-many dependency between objects so that when one object changes state, all its dependents are notified and updated automatically.

```python
class Observer:
    """The event notification system using the Observer pattern."""
    
    def __init__(self):
        self._subscribers = defaultdict(list)
        
    def subscribe(self, event_type, callback):
        """Subscribe to an event type with a callback function."""
        self._subscribers[event_type].append(callback)
        
    def unsubscribe(self, event_type, callback):
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)
            
    def notify(self, event_type, data=None):
        """Notify all subscribers of an event."""
        for callback in self._subscribers.get(event_type, []):
            callback(data)
```

**Usage Example**:

```python
# Create a notification center
notification_center = Observer()

# Define subscribers
def email_notification(data):
    send_email(data['recipient'], "Transaction Alert", data['message'])

def sms_notification(data):
    send_sms(data['phone'], data['message'])

def audit_log(data):
    log_entry = f"Transaction {data['transaction_id']}: {data['amount']}"
    write_audit_log(log_entry)

# Subscribe to events
notification_center.subscribe("transaction.completed", email_notification)
notification_center.subscribe("transaction.completed", sms_notification)
notification_center.subscribe("transaction.completed", audit_log)

# Notify subscribers when a transaction is completed
notification_center.notify("transaction.completed", {
    "transaction_id": "TX123456",
    "amount": 1000.00,
    "recipient": "customer@example.com",
    "phone": "+1234567890",
    "message": "Your transaction of $1000.00 has been completed."
})
```

#### Strategy Pattern

The Strategy pattern defines a family of algorithms, encapsulates each one, and makes them interchangeable. It lets the algorithm vary independently from clients that use it.

```python
class Strategy:
    """Interface for strategies."""
    
    def execute(self, data):
        raise NotImplementedError

class ConcreteStrategyA(Strategy):
    """Concrete implementation of Strategy A."""
    
    def execute(self, data):
        return sorted(data)

class ConcreteStrategyB(Strategy):
    """Concrete implementation of Strategy B."""
    
    def execute(self, data):
        return sorted(data, reverse=True)

class Context:
    """Context that uses a strategy."""
    
    def __init__(self, strategy=None):
        self._strategy = strategy
        
    @property
    def strategy(self):
        return self._strategy
        
    @strategy.setter
    def strategy(self, strategy):
        self._strategy = strategy
        
    def execute_strategy(self, data):
        if self._strategy is None:
            raise ValueError("Strategy not set")
        return self._strategy.execute(data)
```

**Usage Example**:

```python
# Using different payment processing strategies
class PaymentProcessor:
    def __init__(self, strategy=None):
        self._strategy = strategy
        
    @property
    def strategy(self):
        return self._strategy
        
    @strategy.setter
    def strategy(self, strategy):
        self._strategy = strategy
        
    def process_payment(self, payment_data):
        return self._strategy.process(payment_data)

# Concrete payment strategies
class CardPaymentStrategy(PaymentStrategy):
    def process(self, payment_data):
        # Process card payment
        return {"status": "success", "method": "card", "id": "CARD123"}

class UpiPaymentStrategy(PaymentStrategy):
    def process(self, payment_data):
        # Process UPI payment
        return {"status": "success", "method": "upi", "id": "UPI456"}

# Usage
processor = PaymentProcessor()

# Set strategy based on payment method
if payment_data["method"] == "card":
    processor.strategy = CardPaymentStrategy()
else:
    processor.strategy = UpiPaymentStrategy()

result = processor.process_payment(payment_data)
```

#### Command Pattern

The Command pattern turns a request into a stand-alone object that contains all information about the request. This allows for parameterization of clients with different requests, queue or log requests, and support undoable operations.

```python
class Command:
    """Interface for commands."""
    
    def execute(self):
        raise NotImplementedError

class SimpleCommand(Command):
    """A simple command with no parameters."""
    
    def __init__(self, receiver, action):
        self._receiver = receiver
        self._action = action
        
    def execute(self):
        return self._receiver.__getattribute__(self._action)()

class ComplexCommand(Command):
    """Complex command with parameters."""
    
    def __init__(self, receiver, action, **kwargs):
        self._receiver = receiver
        self._action = action
        self._kwargs = kwargs
        
    def execute(self):
        return self._receiver.__getattribute__(self._action)(**self._kwargs)

class CommandInvoker:
    """Invoker that executes commands."""
    
    def __init__(self):
        self._commands = []
        
    def add_command(self, command):
        self._commands.append(command)
        
    def execute_commands(self):
        results = []
        for command in self._commands:
            results.append(command.execute())
        self._commands = []
        return results
```

**Usage Example**:

```python
# Creating a transaction processing system with commands
class Account:
    def __init__(self, account_id, balance=0):
        self.account_id = account_id
        self.balance = balance
        
    def deposit(self, amount):
        self.balance += amount
        return f"Deposited {amount}, new balance: {self.balance}"
        
    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        return f"Withdrew {amount}, new balance: {self.balance}"

# Create commands
account = Account("123456", 1000)
deposit_cmd = ComplexCommand(account, "deposit", amount=500)
withdraw_cmd = ComplexCommand(account, "withdraw", amount=200)

# Execute commands
invoker = CommandInvoker()
invoker.add_command(deposit_cmd)
invoker.add_command(withdraw_cmd)
results = invoker.execute_commands()
```

#### Chain of Responsibility Pattern

The Chain of Responsibility pattern passes requests along a chain of handlers. Each handler decides either to process the request or to pass it to the next handler in the chain.

```python
class Handler:
    """Base Handler class for Chain of Responsibility pattern."""
    
    def __init__(self):
        self._next_handler = None
        
    def set_next(self, handler):
        self._next_handler = handler
        return handler
        
    def handle(self, request):
        if self._next_handler:
            return self._next_handler.handle(request)
        return None

class ConcreteHandlerA(Handler):
    """Concrete handler that processes specific requests."""
    
    def handle(self, request):
        if self.can_handle(request):
            # Handle the request
            return f"ConcreteHandlerA: {request}"
        return super().handle(request)
        
    def can_handle(self, request):
        # Check if this handler can process the request
        return "A" in request

class ConcreteHandlerB(Handler):
    """Another concrete handler."""
    
    def handle(self, request):
        if self.can_handle(request):
            return f"ConcreteHandlerB: {request}"
        return super().handle(request)
        
    def can_handle(self, request):
        return "B" in request
```

**Usage Example**:

```python
# Creating an authorization chain
class AuthorizationHandler(Handler):
    def handle(self, request):
        # Base implementation
        return super().handle(request)

class RoleHandler(AuthorizationHandler):
    def __init__(self, required_role):
        super().__init__()
        self.required_role = required_role
        
    def handle(self, request):
        if not request.user.has_role(self.required_role):
            return {"authorized": False, "reason": f"Missing required role: {self.required_role}"}
        return super().handle(request)

class PermissionHandler(AuthorizationHandler):
    def __init__(self, required_permission):
        super().__init__()
        self.required_permission = required_permission
        
    def handle(self, request):
        if not request.user.has_permission(self.required_permission):
            return {"authorized": False, "reason": f"Missing required permission: {self.required_permission}"}
        return super().handle(request)

class IPWhitelistHandler(AuthorizationHandler):
    def __init__(self, allowed_ips):
        super().__init__()
        self.allowed_ips = allowed_ips
        
    def handle(self, request):
        if request.ip not in self.allowed_ips:
            return {"authorized": False, "reason": "IP address not whitelisted"}
        return super().handle(request)

# Set up the chain
admin_chain = RoleHandler("admin")
admin_chain.set_next(PermissionHandler("delete_users"))

# Final handler for successful authorization
class SuccessHandler(AuthorizationHandler):
    def handle(self, request):
        return {"authorized": True}

admin_chain.set_next(SuccessHandler())

# Use the chain
result = admin_chain.handle(request)
```

### 4. Utility Decorators

#### Memoize Decorator

The Memoize decorator caches function results based on arguments to avoid redundant calculations.

```python
def memoize(func):
    """Cache the results of a function based on its arguments."""
    cache = {}
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create a key from the function arguments
        key = str(args) + str(kwargs)
        
        if key not in cache:
            cache[key] = func(*args, **kwargs)
            
        return cache[key]
        
    return wrapper
```

**Usage Example**:

```python
@memoize
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

@memoize
def get_account_details(account_id):
    # This would normally query the database
    return database.query("SELECT * FROM accounts WHERE id = %s", account_id)
```

#### Retry Decorator

The Retry decorator automatically retries a function if it raises certain exceptions.

```python
def retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,)):
    """Retry a function if it raises specified exceptions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt == max_attempts:
                        raise
                        
                    # Log the retry attempt
                    logger.warning(
                        f"Retry {attempt}/{max_attempts} for {func.__name__} "
                        f"after {current_delay}s due to {e.__class__.__name__}: {str(e)}"
                    )
                    
                    # Wait before retrying
                    time.sleep(current_delay)
                    current_delay *= backoff
                    
        return wrapper
    return decorator
```

**Usage Example**:

```python
@retry(max_attempts=5, delay=0.5, backoff=2, exceptions=(ConnectionError, Timeout))
def fetch_external_api_data(api_url):
    response = requests.get(api_url, timeout=2)
    response.raise_for_status()
    return response.json()

@retry(max_attempts=3, exceptions=(DatabaseConnectionError,))
def save_transaction(transaction):
    return database.execute(
        "INSERT INTO transactions (account_id, amount, type) VALUES (%s, %s, %s)",
        transaction.account_id, transaction.amount, transaction.type
    )
```

#### Method Timer Decorator

The Method Timer decorator measures and logs the execution time of functions.

```python
def method_timer(func):
    """Measure and log the execution time of a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
        
        return result
    return wrapper
```

**Usage Example**:

```python
@method_timer
def generate_monthly_report():
    # Report generation code
    pass

@method_timer
def process_bulk_transactions(transactions):
    for transaction in transactions:
        process_transaction(transaction)
```

## Design Pattern Selection Guidelines

When deciding which design pattern to use, consider the following guidelines:

1. **Singleton Pattern**:
   - Use when exactly one instance of a class is needed
   - Use for resources that are expensive to create
   - Use for shared resources like configuration, connection pools, or caches

2. **Factory Pattern**:
   - Use when the exact type of object to create is determined at runtime
   - Use when you want to centralize object creation logic
   - Use when you need to create objects without exposing creation logic

3. **Observer Pattern**:
   - Use when changes to one object require changing others
   - Use when an object should notify an unknown set of objects
   - Use for implementing event handling systems

4. **Strategy Pattern**:
   - Use when you have multiple algorithms for a specific task
   - Use when you need to switch algorithms at runtime
   - Use when you want to isolate the logic of an algorithm from its implementation

5. **Adapter Pattern**:
   - Use when you need to make incompatible interfaces work together
   - Use when integrating with legacy code or third-party libraries
   - Use during migration to new interfaces

6. **Command Pattern**:
   - Use when you want to parameterize objects with operations
   - Use when you need to queue operations or implement undo/redo
   - Use when you need to support logging or transactional operations

## Integration with Other Components

### Integration with Dependency Injection

Design patterns work well with the dependency injection system:

```python
# Register singleton in the DI container
container.register_singleton(ConfigService, ConfigService)

# Register strategies in the DI container
container.register("card_payment", CardPaymentStrategy)
container.register("upi_payment", UpiPaymentStrategy)

# Resolve based on configuration
payment_strategy = container.resolve(config.get("payment_method"))
```

### Integration with Error Handling

Design patterns can enhance error handling:

```python
# Command pattern with error handling
class TransactionCommand(Command):
    def execute(self):
        try:
            return self._receiver.process_transaction(self._transaction)
        except InsufficientFundsException as e:
            # Handle specific exception
            return {"status": "error", "code": "insufficient_funds", "message": str(e)}
        except CBSException as e:
            # Handle general CBS exception
            return e.to_dict()
```

## Best Practices

1. **Choose the Right Pattern**: Select patterns appropriate for the specific problem.
2. **Don't Overuse Patterns**: Use patterns only when they provide clear benefits.
3. **Keep It Simple**: Start with the simplest solution and apply patterns as needed.
4. **Document Usage**: Clearly document where and why patterns are used.
5. **Consistent Implementation**: Use consistent implementations across the codebase.
6. **Test Pattern Implementations**: Thoroughly test design pattern implementations.

## Conclusion

The design patterns implemented in the CBS_PYTHON system provide standardized solutions to common design problems, promoting code reuse and maintainability. By using these patterns appropriately, developers can create more flexible and modular code that's easier to understand, maintain, and extend.

Last updated: May 23, 2025
