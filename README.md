# 🏦 CBS_PYTHON: Core Banking System

[![Status: Planning](https://img.shields.io/badge/Status-Planning-blue)](https://github.com/Soumya-r-Sahu/CBS_PYTHON)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-black?logo=github)](https://github.com/Soumya-r-Sahu/CBS_PYTHON)

---

![Version 1.1.0](https://img.shields.io/badge/Version-1.1.0-brightgreen) 

_Last updated: May 17, 2025_

---

## 1️⃣ Project Overview

CBS_PYTHON is a modular, domain-driven Core Banking System designed for extensibility, security, and modern banking needs.
- 🏗️ **Clean Architecture** (Domain, Application, Infrastructure, Presentation)
- 🧩 **Modular Domains** (Accounts, Customers, Loans, Transactions, UPI, etc.)
- 🖥️ **Multi-Interface**: API, CLI, GUI, Admin Dashboard, ATM/UPI
- 🔒 **Security**: Encryption, access control, audit trails
- 📊 **Analytics & BI**: Real-time dashboards, fraud detection
- 📚 **Comprehensive Documentation**

## 2️⃣ Configuration

Before running the system, configure your environment:
- ⚙️ **Database**: Edit `config.py` or `app/config/settings.yaml` for DB settings
- 🔑 **Secrets**: Set up environment variables or `.env` for sensitive data
- 🛡️ **Security**: Review `security/` for encryption and access control settings
- 📝 **Modules**: Ensure all modules have `__init__.py` and correct import paths

---

## ✨ Project Highlights

| Feature                | Status      | Progress |
|------------------------|-------------|----------|
| Clean Architecture     | 🟡 In Progress | 🟨🟨🟨🟨🟨🟨⬜⬜⬜⬜ 60% |
| Modular Domains        | ✅ Complete | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% |
| CLI Interface          | ✅ Complete | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% |
| GUI                    | 🟡 In Progress | 🟨🟨🟨🟨⬜⬜⬜⬜⬜⬜ 40% |
| API Layer              | ✅ Complete | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% |
| Documentation          | 🟡 In Progress | 🟨🟨🟨🟨🟨🟨🟨⬜⬜⬜ 70% |

---

## ⚡ Quick Setup

```bash
# Clone the repo
git clone https://github.com/Soumya-r-Sahu/CBS_PYTHON.git
cd CBS_PYTHON

# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python main.py --init-db

# Run the system
python main.py --mode api --env development
```

---

## 🗺️ Module Progress

| Module             | Status        | Progress |
|--------------------|--------------|----------|
| Accounts           | ✅ Complete   | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% |
| Customers          | ✅ Complete   | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% |
| Loans              | ✅ Complete   | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% |
| Transactions       | ✅ Complete   | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% |
| ATM                | ✅ Complete   | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% |
| Internet Banking   | 🟠 In Progress| 🟨🟨🟨🟨🟨🟨⬜⬜⬜⬜ 60% |
| Mobile Banking     | 🟠 In Progress| 🟨🟨🟨🟨⬜⬜⬜⬜⬜⬜ 40% |
| UPI                | ✅ Complete   | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% |
| NEFT               | 🟠 In Progress| 🟨🟨🟨⬜⬜⬜⬜⬜⬜⬜ 50% |
| RTGS               | 🟡 Planned    | 🟨⬜⬜⬜⬜⬜⬜⬜⬜⬜ 10% |
| Fraud Detection    | 🟠 In Progress| 🟨🟨⬜⬜⬜⬜⬜⬜⬜⬜ 30% |
| Audit Trail        | ✅ Complete   | 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100% |
| BI Dashboards      | 🟠 In Progress| 🟨⬜⬜⬜⬜⬜⬜⬜⬜⬜ 20% |

---

## 📊 Database Tab

### Key Tables
| Table Name            | Key Columns                                               | Emoji |
|-----------------------|-----------------------------------------------------------|-------|
| customers             | customer_id, name, dob, email, phone, address             | 👤👪 |
| accounts              | account_number, customer_id, balance, type, status        | 💳💰 |
| transactions          | transaction_id, account_number, type, amount, timestamp   | 💸🔄 |
| cards                 | card_id, account_id, card_number, expiry_date, cvv, pin   | 🃏💳 |
| upi_registrations     | upi_id, account_number, linked_device, status, created_at | 📱💲 |
| admins                | admin_id, username, role, email, status, last_login       | 🛠️👨‍💼|
| branches              | branch_id, name, address, contact, manager_id, status     | 🏢🏦 |
| loans                 | loan_id, customer_id, amount, interest_rate, term, status | 💵📝 |
| fixed_deposits        | fd_id, account_id, amount, interest_rate, tenure, maturity| 🏆💹 |
| kyc_documents         | doc_id, customer_id, doc_type, verification_status        | 📄✅ |
| audit_logs            | log_id, user_id, action, timestamp, ip_address, status    | 📋🔍 |

### ER Diagram
```mermaid
erDiagram
    CUSTOMERS ||--o{ ACCOUNTS : has
    CUSTOMERS ||--o{ LOANS : borrows
    ACCOUNTS ||--o{ TRANSACTIONS : generates
    ACCOUNTS ||--o{ CARDS : issues
    ACCOUNTS ||--o{ UPI_REGISTRATIONS : enables
    ACCOUNTS ||--o{ FIXED_DEPOSITS : creates
    BRANCHES ||--o{ ACCOUNTS : manages
    CUSTOMERS ||--o{ KYC_DOCUMENTS : provides
    ADMINS ||--o{ AUDIT_LOGS : creates
```

---

## 🧩 Architecture Overview

```mermaid
graph TD
    A[User/Customer/Employee/Admin] -->|Login| B[Main Menu]
    B -->|ATM| C[ATM Interface]
    B -->|UPI| D[UPI Services]
    B -->|Admin| E[Admin Dashboard]
    B -->|Customer| F[Customer Dashboard]
    C -->|Withdraw/Inquiry| G[Database]
    D -->|Pay/Register| G
    E -->|User Mgmt/Logs| G
    F -->|Account/Fund Transfer| G
    G -->|Show Results| H[Results/Confirmation]
    H -->|Logout| I[End]
    S[Security Layer] -->|Protects| G
    S -->|Authenticates| A
```

---

## 🐞 Troubleshooting Guide

| Problem Type         | Solution/Tip                                              | Emoji  |
|----------------------|----------------------------------------------------------|--------|
| Missing Dependency   | Run `pip install -r requirements.txt`                    | ⚠️     |
| DB Connection Error  | Check DB config in `config.py` or `app/config/settings.yaml` | ❌     |
| Import Error         | Ensure all folders have `__init__.py` and use underscores| 📝     |
| Invalid Input        | Enter valid data, follow prompts                         | 🔄     |
| Unhandled Exception  | Check logs in the `logs/` directory                      | 🚨     |
| Environment Issues   | Run `python scripts/utilities/show_environment.py`        | 🌐     |
| Indentation Errors   | Run `python scripts/utilities/fix_indentation.py`         | 🔧     |
| Module Not Found     | Check installation and import paths                      | 🔄     |

---

## 🏃 How to Run the System

| Step | Command (Windows)                                   | Description                  |
|------|-----------------------------------------------------|------------------------------|
| 1    | `git clone https://github.com/Soumya-r-Sahu/CBS_PYTHON.git` | Clone the repository         |
| 2    | `cd CBS_PYTHON`                                     | Enter project directory      |
| 3    | `python -m venv venv`                               | Create virtual environment   |
| 4    | `.\venv\Scripts\activate`                           | Activate environment         |
| 5    | `pip install -r requirements.txt`                   | Install dependencies         |
| 6    | `python main.py --init-db`                          | Initialize the database      |
| 7    | `python main.py --mode api --env development`       | Run API server (dev mode)    |
| 8    | `python main.py --mode gui --env test`              | Run GUI (test mode)          |
| 9    | `python main.py --mode cli`                         | Run CLI interface            |

---

## 🛠️ Initializing Scripts

- **Database Initialization:**
  - `python main.py --init-db`  
    Initializes all required tables and seeds initial data.
- **Show Current Environment:**
  - `python scripts/utilities/show_environment.py`
- **Fix Indentation:**
  - `python scripts/utilities/fix_indentation.py`

---

## 🏗️ System Flow & Architecture

### System Flow
```mermaid
flowchart TD
    A[User/Customer/Employee/Admin] -->|Login/Access| B[Main Menu]
    B -->|ATM| C[ATM Interface]
    B -->|UPI| D[UPI Services]
    B -->|Admin| E[Admin Dashboard]
    B -->|Customer| F[Customer Dashboard]
    C -->|Withdraw/Inquiry/PIN| G[Database]
    D -->|Pay/Register/QR| G
    E -->|User Mgmt/Logs| G
    F -->|Account/Fund Transfer| G
    G -->|Show Results| H[Results/Confirmation]
    H -->|Logout| I[End]
    S[Security Layer] -->|Protects| G
    S -->|Authenticates| A
```

### Architecture & Interfaces
- **Domain-Oriented, Modular Design**: Each business area is a separate module.
- **Clean Architecture**: Domain, Application, Infrastructure, and Presentation layers.
- **Interfaces**:
  - **API**: RESTful endpoints for all major modules (`run_api.py`)
  - **CLI**: Unified command-line interface (`scripts/cli/cbs_cli`)
  - **GUI**: PyQt5-based desktop apps (`gui/`)
  - **Admin Dashboard**: For user management and logs
  - **ATM/UPI**: Simulated interfaces for digital channels

---

## 🌟 Features at a Glance

| 🏷️ Feature           | 🚦 Status      | 💡 Emoji |
|----------------------|---------------|----------|
| Account Management   | ✅ Complete   | 👤💼     |
| Transaction Engine   | ✅ Complete   | 💸🔄     |
| UPI/NEFT/RTGS        | 🟡 In Progress| 📱💳     |
| Audit Trail          | ✅ Complete   | 📋🕵️     |
| Security             | ✅ Complete   | 🔒       |
| Modular CLI          | ✅ Complete   | 💻⌨️     |
| GUI                  | 🟡 In Progress| 🖥️✨     |
| API Layer            | ✅ Complete   | 🌐🚀     |
| Documentation        | 🟡 In Progress| 📚       |

---

## 📚 Documentation & Guides
- [Implementation Guides](documentation/implementation_guides/)
- [Architecture Diagrams](documentation/architecture_diagrams/)
- [User Manuals](documentation/user_manuals/)
- [API Guides](documentation/api_guides/)

---

## 🛡️ Security Highlights
- Passwords hashed & encrypted
- Sensitive data encrypted at rest
- Access control enforced
- All actions logged for audit

---

## 🔮 Future Updates

| Planned Feature                        | Description                                      | Status      | Emoji |
|----------------------------------------|--------------------------------------------------|-------------|-------|
| Full PyQt5 GUIs for all modules        | ATM, UPI, Customer, Employee, Netbanking         | 🟡 Planned  | 🖥️✨  |
| Enhanced dashboards and monitoring     | Real-time analytics and system health             | 🟡 Planned  | 📊🔔  |
| AI-based fraud detection               | Machine learning for transaction risk             | 🟡 Planned  | 🤖🛡️  |
| Multi-language support                 | UI/CLI/API in multiple languages                  | 🟡 Planned  | 🌐🈳  |
| Real-time third-party API integration  | Connect to external banking/payment APIs          | 🟡 Planned  | 🔌🌍  |
| Advanced error handling and logging    | More robust error recovery and audit trails        | 🟡 Planned  | 🩹📋  |
| Mobile app interface                   | Native mobile banking app                         | 🟡 Planned  | 📱✨  |
| Enhanced dependency management         | Smarter package and module management             | 🟡 Planned  | 📦🧩  |

---

## 🔗 Useful Links
- [Project Repository](https://github.com/Soumya-r-Sahu/CBS_PYTHON)
- [Implementation Roadmap](documentation/implementation_guides/)
- [Clean Architecture Progress](CLEAN_ARCHITECTURE_PROGRESS.md)

---

> © 2025 [Soumya-r-Sahu](https://github.com/Soumya-r-Sahu) | [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
> 
> Made with ❤️ by [Soumya-r-Sahu](https://github.com/Soumya-r-Sahu)
