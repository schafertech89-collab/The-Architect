"""
Structured logging configuration for the Coinbase LangChain Tool Server.
"""

import structlog
import logging
import sys
from typing import Any, Dict
from datetime import datetime

from config import settings


def add_timestamp(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add timestamp to log events."""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def add_service_info(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add service information to log events."""
    event_dict["service"] = "coinbase-langchain-tool-server"
    event_dict["version"] = "1.0.0"
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Add service info and timestamp
            add_service_info,
            add_timestamp,
            # Add log level
            structlog.stdlib.add_log_level,
            # Add logger name
            structlog.stdlib.add_logger_name,
            # Process stack info
            structlog.processors.StackInfoRenderer(),
            # Format exceptions
            structlog.dev.set_exc_info,
            # JSON formatting for production, console for development
            structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL.upper())
        ),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Set up loggers for external libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Create a logger instance to test configuration
    logger = structlog.get_logger(__name__)
    logger.info(
        "Logging configured successfully",
        log_level=settings.LOG_LEVEL,
        debug_mode=settings.DEBUG
    )


class RequestLogger:
    """Custom middleware for request logging."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
    
    async def log_request(self, request, call_next):
        """Log incoming requests."""
        start_time = datetime.utcnow()
        
        # Log request start
        self.logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client_host=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Log response
        self.logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration_seconds=round(duration, 4),
        )
        
        return response


class CoinbaseAuditLogger:
    """Specialized logger for Coinbase API operations."""
    
    def __init__(self):
        self.logger = structlog.get_logger("coinbase_audit")
    
    def log_api_call(self, endpoint: str, method: str, params: Dict[str, Any] = None, 
                    success: bool = True, error: str = None):
        """Log Coinbase API calls for audit purposes."""
        log_data = {
            "event_type": "coinbase_api_call",
            "endpoint": endpoint,
            "method": method,
            "success": success,
        }
        
        if params:
            # Remove sensitive data from logs
            safe_params = {k: v for k, v in params.items() 
                          if k not in ["private_key", "api_key", "passphrase"]}
            log_data["parameters"] = safe_params
        
        if error:
            log_data["error"] = error
        
        if success:
            self.logger.info("Coinbase API call successful", **log_data)
        else:
            self.logger.error("Coinbase API call failed", **log_data)
    
    def log_trade_execution(self, action: str, product_id: str, amount: str, 
                          order_type: str, order_id: str = None, success: bool = True,
                          error: str = None):
        """Log trade execution for audit purposes."""
        log_data = {
            "event_type": "trade_execution",
            "action": action,
            "product_id": product_id,
            "amount": amount,
            "order_type": order_type,
            "success": success,
        }
        
        if order_id:
            log_data["order_id"] = order_id
        
        if error:
            log_data["error"] = error
        
        if success:
            self.logger.info("Trade executed successfully", **log_data)
        else:
            self.logger.error("Trade execution failed", **log_data)


# Global audit logger instance
audit_logger = CoinbaseAuditLogger()
