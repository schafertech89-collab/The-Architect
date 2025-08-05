"""
FastAPI routes for Coinbase LangChain tool server.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
import structlog

from models import (
    BalanceResponse, PortfolioResponse, TradeRequest, TradeResponse,
    OrdersResponse, CancelOrderRequest, HealthResponse
)
from langchain_tools import (
    CoinbaseBalanceTool, CoinbasePortfolioTool, 
    CoinbaseTradeTool, CoinbaseOrdersTool
)
from coinbase_client import CoinbaseError

logger = structlog.get_logger(__name__)

router = APIRouter()

# Initialize tools
balance_tool = CoinbaseBalanceTool()
portfolio_tool = CoinbasePortfolioTool()
trade_tool = CoinbaseTradeTool()
orders_tool = CoinbaseOrdersTool()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for the tool server."""
    return HealthResponse(
        status="healthy",
        service="coinbase-langchain-tool-server",
        tools_available=["balance", "portfolio", "trade", "orders"]
    )


@router.get("/balance", response_model=BalanceResponse)
async def get_balance():
    """
    Get current cryptocurrency balances from Coinbase account.
    This endpoint exposes the LangChain balance tool for ChatGPT integration.
    """
    try:
        logger.info("Balance endpoint called")
        result = await balance_tool._arun()
        
        return BalanceResponse(
            success=True,
            message="Balance retrieved successfully",
            data={"balance_info": result}
        )
        
    except Exception as e:
        logger.error("Balance endpoint error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve balance: {str(e)}"
        )


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio():
    """
    Get detailed portfolio information including holdings and available trading products.
    This endpoint exposes the LangChain portfolio tool for ChatGPT integration.
    """
    try:
        logger.info("Portfolio endpoint called")
        result = await portfolio_tool._arun()
        
        return PortfolioResponse(
            success=True,
            message="Portfolio retrieved successfully",
            data={"portfolio_info": result}
        )
        
    except Exception as e:
        logger.error("Portfolio endpoint error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve portfolio: {str(e)}"
        )


@router.post("/trade", response_model=TradeResponse)
async def execute_trade(trade_request: TradeRequest):
    """
    Execute a cryptocurrency trade on Coinbase.
    This endpoint exposes the LangChain trade tool for ChatGPT integration.
    
    Expected input format matches LangChain tool:
    'action:BUY product:BTC-USD amount:0.001 type:market price:50000'
    """
    try:
        logger.info("Trade endpoint called", trade_data=trade_request.dict())
        
        # Convert request to tool input format
        tool_input = f"action:{trade_request.action} product:{trade_request.product_id} amount:{trade_request.amount} type:{trade_request.order_type}"
        
        if trade_request.price:
            tool_input += f" price:{trade_request.price}"
        
        result = await trade_tool._arun(tool_input)
        
        # Check if trade was successful based on result content
        success = "successfully" in result.lower() and "failed" not in result.lower()
        
        return TradeResponse(
            success=success,
            message="Trade request processed",
            data={"trade_result": result}
        )
        
    except Exception as e:
        logger.error("Trade endpoint error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute trade: {str(e)}"
        )


@router.get("/orders", response_model=OrdersResponse)
async def get_orders(status: Optional[str] = None):
    """
    Get order history and status.
    This endpoint exposes the LangChain orders tool for ChatGPT integration.
    
    Query parameters:
    - status: Filter orders by status ('open', 'all', or None for recent)
    """
    try:
        logger.info("Orders endpoint called", status_filter=status)
        
        # Convert status to tool input format
        tool_input = "list"
        if status == "open":
            tool_input = "open"
        elif status == "all":
            tool_input = "all"
        
        result = await orders_tool._arun(tool_input)
        
        return OrdersResponse(
            success=True,
            message="Orders retrieved successfully",
            data={"orders_info": result}
        )
        
    except Exception as e:
        logger.error("Orders endpoint error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve orders: {str(e)}"
        )


@router.delete("/orders/{order_id}")
async def cancel_order(order_id: str):
    """
    Cancel a specific order by ID.
    This endpoint exposes order cancellation functionality for ChatGPT integration.
    """
    try:
        logger.info("Cancel order endpoint called", order_id=order_id)
        
        # Use orders tool to cancel
        tool_input = f"cancel:{order_id}"
        result = await orders_tool._arun(tool_input)
        
        success = "cancelled successfully" in result.lower()
        
        return {
            "success": success,
            "message": "Order cancellation processed",
            "data": {"cancel_result": result}
        }
        
    except Exception as e:
        logger.error("Cancel order endpoint error", order_id=order_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel order: {str(e)}"
        )


@router.get("/tools")
async def list_tools():
    """
    List all available LangChain tools and their descriptions.
    Useful for ChatGPT to understand available capabilities.
    """
    tools_info = []
    
    for tool in [balance_tool, portfolio_tool, trade_tool, orders_tool]:
        tools_info.append({
            "name": tool.name,
            "description": tool.description,
            "endpoint": f"/api/v1/{tool.name.replace('coinbase_', '')}"
        })
    
    return {
        "success": True,
        "message": "Available tools listed",
        "data": {
            "tools": tools_info,
            "total_count": len(tools_info)
        }
    }


@router.get("/tools/{tool_name}")
async def get_tool_info(tool_name: str):
    """
    Get detailed information about a specific tool.
    """
    tool_map = {
        "balance": balance_tool,
        "portfolio": portfolio_tool,
        "trade": trade_tool,
        "orders": orders_tool
    }
    
    if tool_name not in tool_map:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found. Available tools: {list(tool_map.keys())}"
        )
    
    tool = tool_map[tool_name]
    
    return {
        "success": True,
        "data": {
            "name": tool.name,
            "description": tool.description,
            "endpoint": f"/api/v1/{tool_name}",
            "type": "langchain_tool"
        }
    }
