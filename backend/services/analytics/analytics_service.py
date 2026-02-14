"""
Analytics Service
Revenue tracking, conversion funnel, and business metrics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
import sqlite3

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Analytics Service - Business metrics and revenue tracking
    
    Provides insights into:
    - Revenue (daily, weekly, monthly, MRR)
    - Conversion funnel
    - Payment success rate
    - Product-wise breakdowns
    - User LTV
    """
    
    def __init__(self, session=None):
        self.session = session
    
    def get_revenue_summary(self, days: int = 30) -> Dict:
        """
        Get revenue summary for last N days
        
        Args:
            days: Number of days to analyze
        
        Returns:
            dict: Revenue summary
        """
        from backend.engines.db_engine import get_conn
        
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            conn = get_conn()
            cursor = conn.cursor()
            
            # Total revenue
            cursor.execute("""
                SELECT 
                    COUNT(*) as order_count,
                    SUM(amount) as total_revenue,
                    AVG(amount) as avg_order_value
                FROM payment_orders
                WHERE status = 'SUCCESS'
                AND created_at >= ?
            """, (start_date,))
            
            summary = cursor.fetchone()
            
            # Revenue by product
            cursor.execute("""
                SELECT 
                    product_type,
                    COUNT(*) as count,
                    SUM(amount) as revenue
                FROM payment_orders
                WHERE status = 'SUCCESS'
                AND created_at >= ?
                GROUP BY product_type
            """, (start_date,))
            
            by_product = cursor.fetchall()
            
            # Daily revenue (last 7 days)
            cursor.execute("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as orders,
                    SUM(amount) as revenue
                FROM payment_orders
                WHERE status = 'SUCCESS'
                AND created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                LIMIT 7
            """, (datetime.now() - timedelta(days=7),))
            
            daily_revenue = cursor.fetchall()
            
            conn.close()
            
            return {
                "period_days": days,
                "total_revenue": float(summary["total_revenue"] or 0),
                "order_count": summary["order_count"] or 0,
                "avg_order_value": float(summary["avg_order_value"] or 0),
                "by_product": [
                    {
                        "product": row["product_type"],
                        "count": row["count"],
                        "revenue": float(row["revenue"])
                    }
                    for row in by_product
                ],
                "daily_revenue": [
                    {
                        "date": row["date"],
                        "orders": row["orders"],
                        "revenue": float(row["revenue"])
                    }
                    for row in daily_revenue
                ]
            }
        
        except Exception as e:
            logger.error(f"❌ Error getting revenue summary: {e}")
            return {}
    
    def get_mrr(self) -> float:
        """
        Calculate Monthly Recurring Revenue (MRR)
        
        For non-subscription model, this is the 30-day trailing average
        
        Returns:
            float: MRR in INR
        """
        from backend.engines.db_engine import get_conn
        
        try:
            start_date = datetime.now() - timedelta(days=30)
            
            conn = get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT SUM(amount) as revenue
                FROM payment_orders
                WHERE status = 'SUCCESS'
                AND created_at >= ?
            """, (start_date,))
            
            result = cursor.fetchone()
            conn.close()
            
            revenue_30_days = float(result["revenue"] or 0)
            mrr = revenue_30_days  # For simplicity, 30-day revenue = MRR
            
            logger.info(f"📊 MRR: ₹{mrr:,.2f}")
            return mrr
        
        except Exception as e:
            logger.error(f"❌ Error calculating MRR: {e}")
            return 0.0
    
    def get_conversion_funnel(self) -> Dict:
        """
        Get conversion funnel metrics
        
        Returns:
            dict: Funnel data (viewed → initiated → paid)
        """
        from backend.engines.db_engine import get_conn
        
        try:
            conn = get_conn()
            cursor = conn.cursor()
            
            # Orders initiated
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM payment_orders
                WHERE created_at >= date('now', '-30 days')
            """)
            initiated = cursor.fetchone()["count"]
            
            # Orders paid
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM payment_orders
                WHERE status = 'SUCCESS'
                AND created_at >= date('now', '-30 days')
            """)
            paid = cursor.fetchone()["count"]
            
            # Orders failed
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM payment_orders
                WHERE status = 'FAILED'
                AND created_at >= date('now', '-30 days')
            """)
            failed = cursor.fetchone()["count"]
            
            conn.close()
            
            # Calculate conversion rate
            conversion_rate = (paid / initiated * 100) if initiated > 0 else 0
            
            return {
                "initiated": initiated,
                "paid": paid,
                "failed": failed,
                "abandoned": initiated - paid - failed,
                "conversion_rate": round(conversion_rate, 2),
                "success_rate": round((paid / initiated * 100) if initiated > 0 else 0, 2)
            }
        
        except Exception as e:
            logger.error(f"❌ Error getting conversion funnel: {e}")
            return {}
    
    def get_payment_success_rate(self, days: int = 7) -> Dict:
        """
        Get payment success rate
        
        Args:
            days: Number of days to analyze
        
        Returns:
            dict: Success rate metrics
        """
        from backend.engines.db_engine import get_conn
        
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            conn = get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM payment_orders
                WHERE created_at >= ?
                GROUP BY status
            """, (start_date,))
            
            status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}
            
            total = sum(status_counts.values())
            success = status_counts.get("SUCCESS", 0)
            failed = status_counts.get("FAILED", 0)
            
            # Get failure reasons
            cursor.execute("""
                SELECT 
                    error_code,
                    COUNT(*) as count
                FROM payment_orders
                WHERE status = 'FAILED'
                AND created_at >= ?
                AND error_code IS NOT NULL
                GROUP BY error_code
                ORDER BY count DESC
                LIMIT 5
            """, (start_date,))
            
            failure_reasons = cursor.fetchall()
            
            conn.close()
            
            return {
                "total_attempts": total,
                "successful": success,
                "failed": failed,
                "success_rate": round((success / total * 100) if total > 0 else 0, 2),
                "failure_rate": round((failed / total * 100) if total > 0 else 0, 2),
                "top_failure_reasons": [
                    {
                        "error_code": row["error_code"],
                        "count": row["count"]
                    }
                    for row in failure_reasons
                ]
            }
        
        except Exception as e:
            logger.error(f"❌ Error getting success rate: {e}")
            return {}
    
    def get_user_ltv(self, phone: str = None) -> Dict:
        """
        Calculate User Lifetime Value
        
        Args:
            phone: Specific user (optional, None for average)
        
        Returns:
            dict: LTV metrics
        """
        from backend.engines.db_engine import get_conn
        
        try:
            conn = get_conn()
            cursor = conn.cursor()
            
            if phone:
                # Specific user LTV
                cursor.execute("""
                    SELECT 
                        phone,
                        COUNT(*) as order_count,
                        SUM(amount) as total_spent,
                        AVG(amount) as avg_order_value,
                        MIN(created_at) as first_order,
                        MAX(created_at) as last_order
                    FROM payment_orders
                    WHERE status = 'SUCCESS'
                    AND phone = ?
                    GROUP BY phone
                """, (phone,))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        "phone": result["phone"],
                        "ltv": float(result["total_spent"]),
                        "order_count": result["order_count"],
                        "avg_order_value": float(result["avg_order_value"]),
                        "first_order": result["first_order"],
                        "last_order": result["last_order"]
                    }
                else:
                    return {"phone": phone, "ltv": 0}
            
            else:
                # Average LTV across all users
                cursor.execute("""
                    SELECT 
                        AVG(user_ltv) as avg_ltv,
                        MAX(user_ltv) as max_ltv,
                        MIN(user_ltv) as min_ltv
                    FROM (
                        SELECT 
                            phone,
                            SUM(amount) as user_ltv
                        FROM payment_orders
                        WHERE status = 'SUCCESS'
                        GROUP BY phone
                    )
                """)
                
                result = cursor.fetchone()
                conn.close()
                
                return {
                    "average_ltv": float(result["avg_ltv"] or 0),
                    "max_ltv": float(result["max_ltv"] or 0),
                    "min_ltv": float(result["min_ltv"] or 0)
                }
        
        except Exception as e:
            logger.error(f"❌ Error calculating LTV: {e}")
            return {}
    
    def get_top_customers(self, limit: int = 10) -> List[Dict]:
        """
        Get top customers by revenue
        
        Args:
            limit: Number of customers to return
        
        Returns:
            list: Top customers
        """
        from backend.engines.db_engine import get_conn
        
        try:
            conn = get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    phone,
                    COUNT(*) as order_count,
                    SUM(amount) as total_spent,
                    MAX(created_at) as last_order
                FROM payment_orders
                WHERE status = 'SUCCESS'
                GROUP BY phone
                ORDER BY total_spent DESC
                LIMIT ?
            """, (limit,))
            
            customers = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "phone": row["phone"],
                    "order_count": row["order_count"],
                    "total_spent": float(row["total_spent"]),
                    "last_order": row["last_order"]
                }
                for row in customers
            ]
        
        except Exception as e:
            logger.error(f"❌ Error getting top customers: {e}")
            return []
    
    def get_dashboard_stats(self) -> Dict:
        """
        Get complete dashboard statistics
        
        Returns:
            dict: All key metrics for admin dashboard
        """
        return {
            "revenue_summary": self.get_revenue_summary(days=30),
            "mrr": self.get_mrr(),
            "conversion_funnel": self.get_conversion_funnel(),
            "success_rate": self.get_payment_success_rate(days=7),
            "average_ltv": self.get_user_ltv(),
            "top_customers": self.get_top_customers(limit=10)
        }


# Singleton
_analytics_service = None

def get_analytics_service() -> AnalyticsService:
    """Get analytics service instance"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service