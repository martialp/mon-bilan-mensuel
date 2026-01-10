# Product Overview

## Personal Finance Tracker

A full-stack web application for managing personal finances, specifically designed to extract and categorize transactions from Desjardins (Quebec credit union) PDF statements.

### Core Features

- **PDF Transaction Extraction**: Uses Claude Vision API to extract transaction data from bank statement PDFs
- **AI-Powered Categorization**: Automatically categorizes transactions using natural language rules
- **Multi-Account Management**: Supports credit cards, chequing, savings, and investment accounts
- **Validation Workflow**: Transactions are auto-categorized then manually confirmed or corrected by users
- **User Management**: Multi-user system with authentication and role-based access

### Business Logic

- Transactions are stored with positive amounts, with type (expense/income/transfer) determining the sign
- Each transaction has a status: auto (AI-categorized), confirmed (user-approved), or manual (user-entered)
- Duplicate prevention using unique constraints on account, date, description, amount, and statement date
- Categories are shared across all users for consistency