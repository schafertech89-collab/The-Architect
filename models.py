"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum


class TradeAction(str, Enum):
    """Valid trade actions."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Valid order types."""
    MARKET = "market"
    LIMIT = "limit"


class BaseResponse(BaseModel):
    """Base response model."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    tools_available: List[str]


class BalanceResponse(BaseResponse):
    """Response model for balance endpoint."""
    pass


class PortfolioResponse(BaseResponse):
    """Response model for portfolio endpoint."""
    pass


class TradeRequest(BaseModel):
    """Request model for trade execution."""
    action: TradeAction = Field(..., description="Buy or sell action")
    product_id: str = Field(..., description="Trading pair (e.g., BTC-USD)")
    amount: str = Field(..., description="Amount to trade")
    order_type: OrderType = Field(default=OrderType.MARKET, description="Order type")
    price: Optional[str] = Field(None, description="Price for limit orders")
    
    class Config:
        schema_extra = {
            "example": {
                "action": "BUY",
                "product_id": "BTC-USD",
                "amount": "0.001",
                "order_type": "market"
            }
        }


class TradeResponse(BaseResponse):
    """Response model for trade execution."""
    pass


class OrdersResponse(BaseResponse):
    """Response model for orders endpoint."""
    pass


class CancelOrderRequest(BaseModel):
    """Request model for order cancellation."""
    order_id: str = Field(..., description="Order ID to cancel")


class ToolInfo(BaseModel):
    """Model for tool information."""
    name: str
    description: str
    endpoint: str
    type: str = "langchain_tool"


class ToolsListResponse(BaseResponse):
    """Response model for tools listing."""
    pass


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str
    error_type: Optional[str] = None
    timestamp: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Failed to execute trade: Invalid product ID",
                "error_type": "CoinbaseError",
                "timestamp": "2025-08-04T12:00:00Z"
            }
        }
