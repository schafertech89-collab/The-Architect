"""
LangChain tools for Coinbase crypto trading operations.
"""

from typing import Dict, List, Optional, Any
from langchain.tools import BaseTool
from pydantic import Field
import structlog

from coinbase_client import CoinbaseClient, CoinbaseError

logger = structlog.get_logger(__name__)


class CoinbaseBalanceTool(BaseTool):
    """Tool to check Coinbase account balances."""
    
    name: str = "coinbase_balance"
    description: str = "Get current cryptocurrency balances from Coinbase account. Returns all account balances with available and hold amounts."
    
    coinbase_client: CoinbaseClient = Field(default_factory=CoinbaseClient)
    
    class Config:
        arbitrary_types_allowed = True
    
    async def _arun(self, query: str = "") -> str:
        """Async implementation to get account balances."""
        try:
            accounts = await self.coinbase_client.get_accounts()
            
            # Filter accounts with non-zero balances
            active_accounts = []
            for account in accounts:
                balance = float(account.get("available_balance", {}).get("value", "0"))
                hold = float(account.get("hold", {}).get("value", "0"))
                
                if balance > 0 or hold > 0:
                    active_accounts.append({
                        "currency": account.get("currency"),
                        "available": f"{balance:.8f}",
                        "hold": f"{hold:.8f}",
                        "total": f"{balance + hold:.8f}"
                    })
            
            if not active_accounts:
                return "No cryptocurrency balances found in your Coinbase account."
            
            result = "Current Coinbase Account Balances:\n"
            for account in active_accounts:
                result += f"- {account['currency']}: {account['available']} available, {account['hold']} on hold (Total: {account['total']})\n"
            
            logger.info("Balance check completed", active_accounts=len(active_accounts))
            return result
            
        except CoinbaseError as e:
            error_msg = f"Failed to retrieve balances: {str(e)}"
            logger.error("Balance tool error", error=str(e))
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error retrieving balances: {str(e)}"
            logger.error("Balance tool unexpected error", error=str(e))
            return error_msg
    
    def _run(self, query: str = "") -> str:
        """Sync wrapper (not implemented for async client)."""
        return "This tool requires async execution. Use _arun instead."


class CoinbasePortfolioTool(BaseTool):
    """Tool to view Coinbase portfolio and trading products."""
    
    name: str = "coinbase_portfolio"
    description: str = "Get detailed portfolio information including available trading products and account overview."
    
    coinbase_client: CoinbaseClient = Field(default_factory=CoinbaseClient)
    
    class Config:
        arbitrary_types_allowed = True
    
    async def _arun(self, query: str = "") -> str:
        """Async implementation to get portfolio information."""
        try:
            # Get accounts and products concurrently would be ideal, but keeping simple
            accounts = await self.coinbase_client.get_accounts()
            products = await self.coinbase_client.get_products()
            
            # Process accounts
            total_value_usd = 0
            active_holdings = []
            
            for account in accounts:
                balance = float(account.get("available_balance", {}).get("value", "0"))
                currency = account.get("currency")
                
                if balance > 0:
                    active_holdings.append({
                        "currency": currency,
                        "balance": f"{balance:.8f}",
                        "account_id": account.get("uuid")
                    })
            
            # Process available products (trading pairs)
            trading_pairs = []
            for product in products[:20]:  # Limit to first 20 for readability
                if product.get("status") == "online":
                    trading_pairs.append({
                        "id": product.get("product_id"),
                        "base": product.get("base_currency"),
                        "quote": product.get("quote_currency"),
                        "min_size": product.get("base_min_size")
                    })
            
            # Build response
            result = "Coinbase Portfolio Overview:\n\n"
            
            # Holdings section
            result += "Active Holdings:\n"
            if active_holdings:
                for holding in active_holdings:
                    result += f"- {holding['currency']}: {holding['balance']}\n"
            else:
                result += "- No active holdings found\n"
            
            # Trading pairs section
            result += f"\nAvailable Trading Pairs (showing first {len(trading_pairs)}):\n"
            for pair in trading_pairs[:10]:  # Show top 10
                result += f"- {pair['id']} (min: {pair['min_size']} {pair['base']})\n"
            
            logger.info("Portfolio overview completed", 
                       holdings=len(active_holdings), 
                       trading_pairs=len(trading_pairs))
            return result
            
        except CoinbaseError as e:
            error_msg = f"Failed to retrieve portfolio: {str(e)}"
            logger.error("Portfolio tool error", error=str(e))
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error retrieving portfolio: {str(e)}"
            logger.error("Portfolio tool unexpected error", error=str(e))
            return error_msg
    
    def _run(self, query: str = "") -> str:
        """Sync wrapper (not implemented for async client)."""
        return "This tool requires async execution. Use _arun instead."


class CoinbaseTradeTool(BaseTool):
    """Tool to execute cryptocurrency trades on Coinbase."""
    
    name: str = "coinbase_trade"
    description: str = """Execute cryptocurrency trades on Coinbase. 
    Input should be in format: 'action:BUY/SELL product:BTC-USD amount:0.001 type:market/limit price:50000'
    - action: BUY or SELL
    - product: Trading pair (e.g., BTC-USD, ETH-USD)
    - amount: Amount to trade
    - type: market or limit order
    - price: Required for limit orders only"""
    
    coinbase_client: CoinbaseClient = Field(default_factory=CoinbaseClient)
    
    class Config:
        arbitrary_types_allowed = True
    
    def _parse_trade_input(self, query: str) -> Dict[str, str]:
        """Parse trade input string into components."""
        params = {}
        parts = query.split()
        
        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)
                params[key.lower()] = value.upper() if key.lower() == "action" else value
        
        return params
    
    async def _arun(self, query: str) -> str:
        """Async implementation to execute trades."""
        try:
            # Parse input parameters
            params = self._parse_trade_input(query)
            
            # Validate required parameters
            required_params = ["action", "product", "amount", "type"]
            missing_params = [p for p in required_params if p not in params]
            
            if missing_params:
                return f"Missing required parameters: {', '.join(missing_params)}. Use format: 'action:BUY product:BTC-USD amount:0.001 type:market'"
            
            action = params["action"]
            product_id = params["product"]
            amount = params["amount"]
            order_type = params["type"]
            price = params.get("price")
            
            # Validate action
            if action not in ["BUY", "SELL"]:
                return "Action must be either BUY or SELL"
            
            # Validate order type
            if order_type not in ["market", "limit"]:
                return "Order type must be either 'market' or 'limit'"
            
            # Validate limit order has price
            if order_type == "limit" and not price:
                return "Limit orders require a price parameter"
            
            # Execute the trade
            order = await self.coinbase_client.place_order(
                product_id=product_id,
                side=action.lower(),
                order_type=order_type,
                size=amount,
                price=price if order_type == "limit" else None
            )
            
            order_id = order.get("id")
            status = order.get("status")
            
            result = f"Trade executed successfully!\n"
            result += f"Order ID: {order_id}\n"
            result += f"Action: {action} {amount} {product_id}\n"
            result += f"Type: {order_type.upper()}"
            if price:
                result += f" at ${price}"
            result += f"\nStatus: {status}"
            
            logger.info("Trade executed", 
                       order_id=order_id, action=action, 
                       product=product_id, amount=amount)
            return result
            
        except CoinbaseError as e:
            error_msg = f"Trade failed: {str(e)}"
            logger.error("Trade tool error", error=str(e))
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error executing trade: {str(e)}"
            logger.error("Trade tool unexpected error", error=str(e))
            return error_msg
    
    def _run(self, query: str) -> str:
        """Sync wrapper (not implemented for async client)."""
        return "This tool requires async execution. Use _arun instead."


class CoinbaseOrdersTool(BaseTool):
    """Tool to view and manage Coinbase orders."""
    
    name: str = "coinbase_orders"
    description: str = """View and manage Coinbase orders. 
    Input options:
    - 'list' or 'all': Show all recent orders
    - 'open': Show only open orders
    - 'cancel:ORDER_ID': Cancel a specific order"""
    
    coinbase_client: CoinbaseClient = Field(default_factory=CoinbaseClient)
    
    class Config:
        arbitrary_types_allowed = True
    
    async def _arun(self, query: str = "list") -> str:
        """Async implementation to manage orders."""
        try:
            query = query.strip().lower()
            
            # Handle cancel order
            if query.startswith("cancel:"):
                order_id = query.split(":", 1)[1]
                await self.coinbase_client.cancel_order(order_id)
                logger.info("Order cancelled via tool", order_id=order_id)
                return f"Order {order_id} has been cancelled successfully."
            
            # Handle list orders
            status_filter = None
            if query == "open":
                status_filter = "open"
            
            orders = await self.coinbase_client.get_orders(status=status_filter, limit=20)
            
            if not orders:
                return "No orders found."
            
            result = f"Recent Orders ({len(orders)} found):\n\n"
            
            for order in orders:
                order_id = order.get("id", "N/A")
                product_id = order.get("product_id", "N/A")
                side = order.get("side", "N/A").upper()
                size = order.get("size", "N/A")
                price = order.get("price", "N/A")
                status = order.get("status", "N/A")
                order_type = order.get("type", "N/A")
                
                result += f"ID: {order_id[:8]}...\n"
                result += f"  {side} {size} {product_id}"
                if price != "N/A":
                    result += f" at ${price}"
                result += f"\n  Type: {order_type.upper()}, Status: {status.upper()}\n\n"
            
            logger.info("Orders retrieved via tool", count=len(orders), status=status_filter)
            return result
            
        except CoinbaseError as e:
            error_msg = f"Failed to manage orders: {str(e)}"
            logger.error("Orders tool error", error=str(e))
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error managing orders: {str(e)}"
            logger.error("Orders tool unexpected error", error=str(e))
            return error_msg
    
    def _run(self, query: str = "list") -> str:
        """Sync wrapper (not implemented for async client)."""
        return "This tool requires async execution. Use _arun instead."


# Initialize tools for easy import
coinbase_tools = [
    CoinbaseBalanceTool(),
    CoinbasePortfolioTool(), 
    CoinbaseTradeTool(),
    CoinbaseOrdersTool()
]
