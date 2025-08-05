# Coinbase LangChain Tool Server

## Overview

This project is a FastAPI-based tool server that enables ChatGPT Agent Mode to interact with Coinbase cryptocurrency trading through LangChain orchestration. The server exposes cryptocurrency trading operations as RESTful endpoints, allowing AI agents to check balances, view portfolios, execute trades, and manage orders on the Coinbase Advanced Trade platform.

The application serves as a bridge between AI agents and cryptocurrency trading functionality, providing a secure and structured way to perform trading operations through natural language interactions.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: FastAPI for high-performance async API server
- **Language**: Python with type hints and Pydantic models for data validation
- **Architecture Pattern**: Layered architecture with clear separation of concerns
  - API routes layer (`api_routes.py`)
  - Business logic layer (`langchain_tools.py`) 
  - Data access layer (`coinbase_client.py`)
  - Configuration management (`config.py`)

### LangChain Integration
- **Tool Framework**: Custom LangChain tools extending `BaseTool`
- **Available Tools**: 
  - `CoinbaseBalanceTool` - Account balance checking
  - `CoinbasePortfolioTool` - Portfolio overview
  - `CoinbaseTradeTool` - Trade execution
  - `CoinbaseOrdersTool` - Order management
- **Design Pattern**: Each tool encapsulates specific Coinbase operations and can be used independently or orchestrated together

### API Design
- **REST Architecture**: Standard HTTP methods with JSON request/response
- **Endpoints Structure**: `/api/v1/` prefix with resource-based routing
- **Response Models**: Consistent response structure using Pydantic models
- **Error Handling**: Custom `CoinbaseError` exception with proper HTTP status codes

### Authentication & Security
- **Coinbase API Authentication**: HMAC SHA256 signature-based authentication
- **Environment-based Configuration**: Sensitive credentials managed through environment variables
- **Sandbox Support**: Configurable sandbox/production environment switching
- **CORS**: Configured for ChatGPT integration with appropriate origins

### Configuration Management
- **Settings**: Centralized configuration using Pydantic `BaseSettings`
- **Environment Variables**: `.env` file support with validation
- **Configurable Parameters**: API endpoints, rate limiting, logging levels, sandbox mode

### Logging & Monitoring
- **Structured Logging**: Using `structlog` for consistent, machine-readable logs
- **Log Enrichment**: Automatic timestamp, service info, and request context
- **Health Checks**: Dedicated endpoint for service monitoring
- **Environment-aware**: Different log formats for development vs production

### Error Handling
- **Custom Exceptions**: `CoinbaseError` for API-specific errors
- **HTTP Exception Mapping**: Proper HTTP status codes for different error types
- **Graceful Degradation**: Fallback responses when external services are unavailable

## External Dependencies

### Coinbase Integration
- **Coinbase Advanced Trade API**: Primary cryptocurrency trading platform
- **Authentication**: API key, private key, and passphrase-based authentication
- **Endpoints**: Account management, trading, order management
- **Sandbox Environment**: Testing environment support

### Core Framework Dependencies
- **FastAPI**: Web framework for building APIs
- **LangChain**: Tool orchestration and AI agent integration framework
- **Pydantic**: Data validation and settings management
- **Structlog**: Structured logging library

### HTTP & Networking
- **Requests**: HTTP client for Coinbase API communication
- **Uvicorn**: ASGI server for FastAPI application
- **CORS Middleware**: Cross-origin resource sharing for web integration

### Development & Configuration
- **Python-dotenv**: Environment variable management
- **HMAC/SHA256**: Cryptographic signing for API authentication
- **Base64**: Encoding for API key management

### Potential Future Dependencies
The architecture supports easy integration of:
- Database systems (if persistent storage is needed)
- Redis (for caching and rate limiting)
- Additional cryptocurrency exchanges
- Message queues for async processing
- Authentication providers for user management