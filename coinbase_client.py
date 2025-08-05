"""
Coinbase Advanced Trade API client implementation using official SDK with JWT authentication.
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
import structlog
from pydantic import BaseModel
from coinbase.rest import RESTClient
from coinbase import jwt_generator

from config import settings

logger = structlog.get_logger(__name__)


class CoinbaseError(Exception):
    """Custom exception for Coinbase API errors."""
    pass


class CoinbaseClient:
    """
    Coinbase Advanced Trade API client using official SDK with JWT authentication.
    """
    
    def __init__(self):
        self.api_key = settings.COINBASE_API_KEY
        self.private_key = settings.private_key  # Use the property that checks both env vars
        
        # Check if credentials are properly configured
        if not self.api_key or not self.private_key:
            logger.warning("Coinbase API credentials not configured", 
                         api_key_present=bool(self.api_key),
                         private_key_present=bool(self.private_key))
            self.client = None
        else:
            # Initialize official Coinbase REST client with JWT authentication
            try:
                if settings.COINBASE_SANDBOX:
                    # Sandbox mode
                    self.client = RESTClient(
                        api_key=self.api_key,
                        api_secret=self.private_key,
                        base_url="https://api-public.sandbox.exchange.coinbase.com"
                    )
                else:
                    # Production mode
                    self.client = RESTClient(
                        api_key=self.api_key,
                        api_secret=self.private_key
                    )
                logger.info("Initialized Coinbase REST client successfully")
            except Exception as e:
                logger.error("Failed to initialize Coinbase REST client", error=str(e))
                self.client = None
            
        logger.info("Initialized Coinbase client", 
                   sandbox=settings.COINBASE_SANDBOX,
                   credentials_configured=bool(self.api_key and self.private_key and self.client))
    

    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Get all account balances using official SDK."""
        # Check if client is initialized
        if not self.client:
            raise CoinbaseError("Coinbase API credentials not configured. Please set COINBASE_API_KEY and COINBASE_PRIVATE_KEY environment variables.")
        
        try:
            logger.info("Retrieving accounts using official SDK")
            # Use official SDK method
            response = self.client.get_accounts()
            # The SDK returns a response object with .accounts attribute
            accounts = response.accounts if hasattr(response, 'accounts') else []
            
            logger.info("Retrieved account balances", account_count=len(accounts))
            return [account.__dict__ if hasattr(account, '__dict__') else account for account in accounts]
            
        except Exception as e:
            logger.error("Failed to get account balances", error=str(e))
            raise CoinbaseError(f"Failed to get accounts: {str(e)}")
    
    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """Get specific account details using official SDK."""
        if not self.client:
            raise CoinbaseError("Coinbase API credentials not configured.")
            
        try:
            response = self.client.get_account(account_id)
            # The SDK returns a response object with .account attribute
            account = response.account if hasattr(response, 'account') else {}
            
            logger.info("Retrieved account details", account_id=account_id)
            return account.__dict__ if hasattr(account, '__dict__') else account
            
        except Exception as e:
            logger.error("Failed to get account details", 
                        account_id=account_id, error=str(e))
            raise CoinbaseError(f"Failed to get account {account_id}: {str(e)}")
    
    async def get_products(self) -> List[Dict[str, Any]]:
        """Get available trading products using official SDK."""
        if not self.client:
            raise CoinbaseError("Coinbase API credentials not configured.")
            
        try:
            response = self.client.get_products()
            # The SDK returns a response object with .products attribute
            products = response.products if hasattr(response, 'products') else []
            
            logger.info("Retrieved trading products", product_count=len(products))
            return [product.__dict__ if hasattr(product, '__dict__') else product for product in products]
            
        except Exception as e:
            logger.error("Failed to get products", error=str(e))
            raise CoinbaseError(f"Failed to get products: {str(e)}")
    
    async def place_order(self, product_id: str, side: str, order_type: str, 
                         size: Optional[str] = None, price: Optional[str] = None,
                         funds: Optional[str] = None) -> Dict[str, Any]:
        """Place a trading order using official SDK."""
        if not self.client:
            raise CoinbaseError("Coinbase API credentials not configured.")
            
        order_data = {
            "product_id": product_id,
            "side": side.lower(),
            "order_type": order_type.lower()
        }
        
        if size:
            order_data["base_size"] = size
        if price:
            order_data["limit_price"] = price
        if funds:
            order_data["quote_size"] = funds
        
        try:
            response = self.client.create_order(**order_data)
            order = response.get("order", {})
            
            logger.info("Order placed successfully", 
                       product_id=product_id, side=side, order_type=order_type,
                       order_id=order.get("order_id"))
            return order
            
        except Exception as e:
            logger.error("Failed to place order", 
                        product_id=product_id, side=side, error=str(e))
            raise CoinbaseError(f"Failed to place order: {str(e)}")
    
    async def get_orders(self, status: Optional[str] = None, 
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Get order history using official SDK."""
        if not self.client:
            raise CoinbaseError("Coinbase API credentials not configured.")
            
        try:
            # Build parameters for list_orders
            kwargs = {"limit": limit}
            if status:
                kwargs["order_status"] = status
                
            response = self.client.list_orders(**kwargs)
            # The SDK returns a response object with .orders attribute
            orders = response.orders if hasattr(response, 'orders') else []
            
            logger.info("Retrieved orders", order_count=len(orders), status=status)
            return [order.__dict__ if hasattr(order, '__dict__') else order for order in orders]
            
        except Exception as e:
            logger.error("Failed to get orders", error=str(e))
            raise CoinbaseError(f"Failed to get orders: {str(e)}")
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a specific order using official SDK."""
        if not self.client:
            raise CoinbaseError("Coinbase API credentials not configured.")
            
        try:
            response = self.client.cancel_orders([order_id])
            
            logger.info("Order cancelled successfully", order_id=order_id)
            return response
            
        except Exception as e:
            logger.error("Failed to cancel order", order_id=order_id, error=str(e))
            raise CoinbaseError(f"Failed to cancel order {order_id}: {str(e)}")
