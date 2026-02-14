"""
Boloastro WhatsApp Bot - Main Flask Application
Enhanced version with security, multi-language support, and production-ready features
"""

import logging
from datetime import datetime
from flask import Flask, request, Response
import xml.sax.saxutils as saxutils

from backend.engines.fsm_engine import process_message
from backend.engines.db_engine import init_db
from backend.utils.security import validate_twilio_signature
from backend.utils.rate_limiter import is_rate_limited
from backend.config import settings

from worker.worker import start_worker
from backend.engines.db_engine import init_db


# Admin Dashboard + CSV Export + Auth
from backend.admin.admin_dashboard import analytics_bp
from backend.admin.export_reports import export_bp
from backend.admin.admin_auth import auth_bp


# =========================
# LOGGING SETUP
# =========================

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log") if not settings.DEBUG else logging.StreamHandler(),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# =========================
# APP SETUP
# =========================

app = Flask(__name__)

# 🔐 Secret key from environment (NEVER hardcode!)
app.secret_key = settings.SECRET_KEY

# Configuration
app.config.from_object(settings)



# =========================
# REGISTER ADMIN BLUEPRINTS
# =========================

app.register_blueprint(analytics_bp)
app.register_blueprint(export_bp)
app.register_blueprint(auth_bp)

# Register Analytics API (Phase 2)
try:
    from backend.api.analytics_api import analytics_api
    app.register_blueprint(analytics_api)
    logger.info("✅ Analytics API registered at /api/v1/analytics")
except Exception as e:
    logger.warning(f"⚠️ Analytics API registration failed: {e}")


# =========================
# INIT DB + DATABASE MODELS
# =========================

try:
    # Initialize old db_engine
    init_db()
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")
    raise

# Initialize new database connection with models
try:
    from backend.utils.database import init_database, get_database
    import os
    
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "sqlite:///bot.db")
    
    # Initialize database connection
    db = init_database(database_url, echo=False)
    
    # Create tables for new models
    db.create_all_tables()
    
    logger.info("✅ Database models initialized")
except Exception as e:
    logger.warning(f"⚠️ Database model initialization: {e}")
    # Continue - old db_engine will still work

try:
    start_worker()
    logger.info("✅ Background worker started")
except Exception as e:
    logger.warning(f"⚠️ Worker start failed (non-critical): {e}")


# =========================
# HEALTH CHECK ENDPOINT
# =========================

@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for monitoring and load balancers
    Returns 200 if healthy, 503 if unhealthy
    """
    try:
        from backend.engines.db_engine import get_conn
        
        # Check database connection
        conn = get_conn()
        conn.execute("SELECT 1")
        conn.close()
        db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_healthy = False
    
    # Check Redis (if configured)
    redis_healthy = True
    try:
        if settings.REDIS_URL:
            import redis
            redis_client = redis.from_url(settings.REDIS_URL)
            redis_client.ping()
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        redis_healthy = False
    
    healthy = db_healthy
    
    health_status = {
        "status": "healthy" if healthy else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": db_healthy,
            "redis": redis_healthy,
        },
        "version": "2.0.0",
        "environment": settings.ENV
    }
    
    return health_status, 200 if healthy else 503


# =========================
# ROOT ENDPOINT
# =========================

@app.route("/", methods=["GET"])
def root():
    """Root endpoint - basic info"""
    return {
        "service": "Boloastro WhatsApp Bot",
        "status": "running",
        "version": "2.0.0",
        "endpoints": {
            "webhook": "/bot",
            "health": "/health",
            "admin": "/admin/login"
        }
    }


# =========================
# TWILIO WEBHOOK
# =========================

@app.route("/bot", methods=["POST"])
def bot():
    """
    Main WhatsApp webhook endpoint
    Receives messages from Twilio and processes them
    """
    
    try:
        # 🔐 Validate Twilio signature (CRITICAL SECURITY!)
        #if not validate_twilio_signature(request):
            #logger.warning(f"🚫 Unauthorized request blocked from {request.remote_addr}")
           # return Response("Unauthorized", status=403)
        
        # Temporarily disable Twilio signature validation in development
        if settings.ENVIRONMENT == "production":
         if not validate_twilio_signature(request):
          return Response("Unauthorized", status=403)
        
        # Get message data from Twilio
        body = request.form.get("Body", "").strip()
        user = request.form.get("From", "").strip()
        
        # Validate required fields
        if not body or not user:
            logger.warning(f"❌ Bad request: missing Body or From")
            return Response("Bad request", status=400)
        
        # ⏱ Rate limiting (prevent spam/abuse)
        if is_rate_limited(user):
            logger.info(f"⏳ Rate limit hit for {user}")
            
            wait_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>⏳ कृपया धीरे धीरे संदेश भेजें / Please slow down. Try again in a minute.</Message>
</Response>"""
            
            return Response(wait_twiml, mimetype="application/xml")
        
        # Log incoming message
        logger.info(f"📩 [{user}] {body[:50]}{'...' if len(body) > 50 else ''}")
        
        # 🤖 Process message through FSM engine
        reply_text = process_message(user, body)
        
        # Fallback if no reply
        if not reply_text:
            reply_text = "⚠️ Something went wrong. Please type *START* to begin again."
            logger.error(f"❌ Empty reply for user {user}, message: {body}")
        
        # Escape XML special characters for TwiML
        reply_text = saxutils.escape(reply_text)
        
        # Create TwiML response
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply_text}</Message>
</Response>"""
        
        logger.info(f"📤 [{user}] Response sent ({len(reply_text)} chars)")
        
        return Response(twiml, mimetype="application/xml")
    
    except Exception as e:
        # Log full error for debugging
        logger.exception(f"❌ Webhook error: {e}")
        
        # Return user-friendly error message
        error_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>⚠️ क्षमा करें, एक त्रुटि हुई / Sorry, an error occurred. Please try again or type HELP.</Message>
</Response>"""
        
        return Response(error_twiml, mimetype="application/xml")


# =========================
# HELPERS
# =========================
def check_payment_status(phone):
    """Manual status check if the user types 'DONE'"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as count FROM payment_orders
        WHERE phone=? AND status='SUCCESS'
        AND updated_at >= datetime('now', '-1 day')
    """, (phone,))
    row = cur.fetchone()
    conn.close()
    return (row[0] > 0) if row else False   

# =========================
# RAZORPAY WEBHOOK (for payment notifications)
# =========================

@app.route("/webhook/razorpay", methods=["POST"])
def razorpay_webhook():
    """
    Idempotent Razorpay Webhook Handler
    Prevents race conditions and duplicate payment processing
    """
    from backend.utils.security import verify_razorpay_signature
    from backend.services.webhook_service import WebhookService
    from backend.repositories.webhook_repository import WebhookRepository
    from backend.repositories.order_repository import OrderRepository
    from backend.utils.database import get_database
    import json
    
    # Get raw payload
    payload = request.get_data(as_text=True)
    signature = request.headers.get('X-Razorpay-Signature', '')
    
    # Verify signature
    try:
        if not verify_razorpay_signature(
            payload=payload,
            signature=signature,
            secret=settings.RAZORPAY_WEBHOOK_SECRET
        ):
            logger.warning(f"⚠️ Invalid webhook signature from {request.remote_addr}")
            return {"error": "Invalid signature"}, 401
    except Exception as e:
        logger.error(f"❌ Signature verification failed: {e}")
        return {"error": "Signature verification failed"}, 401
    
    # Parse event
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON in webhook")
        return {"error": "Invalid JSON"}, 400
    
    event_id = event.get("id")
    event_type = event.get("event")
    
    if not event_id:
        logger.error("❌ Missing event ID")
        return {"error": "Missing event ID"}, 400
    
    logger.info(f"📥 Webhook: {event_id} - {event_type}")
    
    # Process idempotently
    try:
        db = get_database()
        
        with db.session_scope() as session:
            webhook_repo = WebhookRepository(session)
            order_repo = OrderRepository(session)
            
            # Entitlement service adapter
            from backend.engines.db_engine import (
                mark_kundali_purchased,
                mark_milan_purchased,
                grant_qna_pack
            )
            
            class EntitlementServiceAdapter:
                def grant(self, user_id, product_type, order_id, metadata=None):
                    phone = user_id if user_id.startswith("whatsapp:") else f"whatsapp:{user_id}"
                    logger.info(f"🎁 Granting {product_type} to {phone}")
                    
                    if product_type == "KUNDALI":
                        mark_kundali_purchased(phone)
                    elif product_type == "MILAN":
                        mark_milan_purchased(phone)
                    elif product_type == "QNA":
                        grant_qna_pack(phone, credits=4)
                
                def revoke(self, user_id, product_type, order_id, reason=None):
                    pass
            
            webhook_service = WebhookService(
                webhook_repo=webhook_repo,
                order_repo=order_repo,
                entitlement_service=EntitlementServiceAdapter()
            )
            
            result = webhook_service.process_event(event_id, event_type, event)
        
        logger.info(f"✅ Webhook processed: {result.get('status')}")
        return {"status": "ok", "result": result}, 200
    
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return {"error": "Internal error", "message": str(e)}, 500

# =========================
# ERROR HANDLERS
# =========================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 error: {request.url}")
    return {"error": "Not found", "status": 404}, 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {error}")
    return {"error": "Internal server error", "status": 500}, 500


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors"""
    logger.warning(f"403 error: {request.url}")
    return {"error": "Forbidden", "status": 403}, 403


# =========================
# BEFORE REQUEST (optional middleware)
# =========================

@app.before_request
def before_request():
    """
    Executed before each request
    Can be used for logging, authentication, etc.
    """
    
    # Log all requests in DEBUG mode
    if settings.DEBUG:
        logger.debug(f"➡️ {request.method} {request.path} from {request.remote_addr}")


# =========================
# AFTER REQUEST (optional middleware)
# =========================

@app.after_request
def after_request(response):
    """
    Executed after each request
    Can be used for headers, CORS, logging, etc.
    """
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Log response in DEBUG mode
    if settings.DEBUG:
        logger.debug(f"⬅️ {response.status_code} {request.path}")
    
    return response

# =========================
# RUN SERVER (development only)
# =========================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 Boloastro WhatsApp Bot Starting...")
    logger.info(f"📍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🐛 Debug Mode: {settings.DEBUG}")
    logger.info(f"📱 WhatsApp: {settings.TWILIO_WHATSAPP_NUMBER}")
    logger.info("=" * 60)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=settings.DEBUG
    )
