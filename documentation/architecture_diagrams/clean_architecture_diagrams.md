# Clean Architecture Diagrams

This document provides visual representations of the Clean Architecture implementation in the CBS_PYTHON project.

---

## 🏗️ Clean Architecture Dependency Flow

```mermaid
graph TD
    subgraph "Entities (Enterprise Business Rules)"
        A[Domain Entities]
        B[Value Objects]
        C[Domain Events]
    end
    subgraph "Use Cases (Application Business Rules)"
        D[Interactors]
        E[Repositories Interfaces]
        F[Services Interfaces]
    end
    subgraph "Interface Adapters"
        G[Controllers]
        H[Presenters]
        I[Repository Implementations]
    end
    subgraph "Frameworks & Drivers"
        J[Web Framework]
        K[Database]
        L[External Services]
    end
    J --> G
    G --> D
    H --> G
    D --> A
    D --> B
    D --> C
    D --> E
    D --> F
    I --> E
    K --> I
    L --> F
    style A fill:#ffcdd2,stroke:#b71c1c
    style B fill:#ffcdd2,stroke:#b71c1c
    style C fill:#ffcdd2,stroke:#b71c1c
    style D fill:#e1bee7,stroke:#4a148c
    style E fill:#e1bee7,stroke:#4a148c
    style F fill:#e1bee7,stroke:#4a148c
    style G fill:#bbdefb,stroke:#0d47a1
    style H fill:#bbdefb,stroke:#0d47a1
    style I fill:#bbdefb,stroke:#0d47a1
    style J fill:#c8e6c9,stroke:#1b5e20
    style K fill:#c8e6c9,stroke:#1b5e20
    style L fill:#c8e6c9,stroke:#1b5e20
```

*This Mermaid diagram illustrates the Clean Architecture dependency flow. Dependencies always point inward, ensuring separation of concerns and testability.*

---

## 📦 CBS Module Architecture Example

```mermaid
graph LR
    subgraph Accounts Module
        A1[Domain Layer] --> A2[Application Layer]
        A2 --> A3[Infrastructure Layer]
        A3 --> A4[Presentation Layer]
    end
    style A1 fill:#ffe082,stroke:#ff6f00
    style A2 fill:#b2dfdb,stroke:#00695c
    style A3 fill:#c5cae9,stroke:#283593
    style A4 fill:#f8bbd0,stroke:#ad1457
```

*This diagram shows the Clean Architecture layering in the Accounts module.*

---

## 🔄 Component Interaction Flow

```mermaid
sequenceDiagram
    participant Client
    participant Controller
    participant UseCase
    participant Entity
    participant Repository
    participant Database
    Client->>Controller: Request
    Controller->>UseCase: Execute use case
    UseCase->>Entity: Manipulate entities
    UseCase->>Repository: Request data
    Repository->>Database: Query/Update data
    Database-->>Repository: Data
    Repository-->>UseCase: Data
    UseCase-->>Controller: Result
    Controller-->>Client: Response
```

*This sequence diagram illustrates the flow of a typical operation across Clean Architecture layers.*

---

## 🧩 Module Relationships

```mermaid
graph TD
    subgraph CoreBanking
        A[Accounts]
        B[Customers]
        C[Loans]
        D[Transactions]
    end
    subgraph DigitalChannels
        E[ATM]
        F[Internet Banking]
        G[Mobile Banking]
    end
    subgraph Payments
        H[UPI]
        I[NEFT]
        J[RTGS]
    end
    subgraph RiskCompliance
        K[Fraud Detection]
        L[Audit Trail]
    end
    A -- provides --> E
    A -- provides --> F
    A -- provides --> G
    D -- supports --> H
    D -- supports --> I
    D -- supports --> J
    B -- referenced by --> D
    C -- referenced by --> D
    K -- monitors --> D
    L -- logs --> D
```

*This diagram shows the relationships between major modules in CBS_PYTHON.*

---

## 📈 Implementation Status (as of May 17, 2025)

| Module                | Status        |
|-----------------------|--------------|
| Accounts              | ✅ Complete   |
| Customers             | ✅ Complete   |
| Loans                 | ✅ Complete   |
| Transactions          | ✅ Complete   |
| ATM                   | ✅ Complete   |
| Internet Banking      | 🟠 In Progress|
| Mobile Banking        | 🟠 In Progress|
| UPI                   | ✅ Complete   |
| NEFT                  | 🟠 In Progress|
| RTGS                  | 🟡 Planned    |
| Fraud Detection       | 🟠 In Progress|
| Audit Trail           | ✅ Complete   |
| BI Dashboards         | 🟠 In Progress|

---

> **Last updated:** May 17, 2025