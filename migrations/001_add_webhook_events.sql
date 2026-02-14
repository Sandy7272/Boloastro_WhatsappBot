-- ================================================
-- Migration: Add Idempotency Support for Webhooks
-- Version: 001
-- Date: 2026-02-13
-- Purpose: Create webhook_events table and update payment_orders table
-- ================================================

-- ================================================
-- CREATE WEBHOOK_EVENTS TABLE
-- ================================================

-- This table stores all webhook events from Razorpay
-- Used for idempotency checking to prevent duplicate processing

CREATE TABLE IF NOT EXISTS webhook_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    order_id VARCHAR(255),
    payload TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    error_message TEXT,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- CREATE INDEXES FOR PERFORMANCE
-- ================================================

-- Unique index on event_id (enforces idempotency)
CREATE UNIQUE INDEX IF NOT EXISTS idx_webhook_event_id 
    ON webhook_events(event_id);

-- Index on status for filtering
CREATE INDEX IF NOT EXISTS idx_webhook_status 
    ON webhook_events(status);

-- Index on order_id for lookups
CREATE INDEX IF NOT EXISTS idx_webhook_order_id 
    ON webhook_events(order_id);

-- Index on created_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_webhook_created 
    ON webhook_events(created_at DESC);

-- Index on event_type for analytics
CREATE INDEX IF NOT EXISTS idx_webhook_event_type 
    ON webhook_events(event_type);

-- ================================================
-- UPDATE PAYMENT_ORDERS TABLE
-- (Add columns if they don't exist)
-- ================================================

-- Note: SQLite doesn't support ALTER COLUMN IF EXISTS
-- We'll try to add columns and ignore errors if they exist

-- Add payment_id column (Razorpay payment ID)
-- This might fail if column exists, that's okay
CREATE TABLE IF NOT EXISTS payment_orders_backup AS 
SELECT * FROM payment_orders;

-- Try to add new columns
-- If column exists, SQLite will give error but won't break
BEGIN TRANSACTION;

-- Add payment_id if missing
ALTER TABLE payment_orders ADD COLUMN payment_id VARCHAR(255);

COMMIT;

BEGIN TRANSACTION;

-- Add error_code if missing
ALTER TABLE payment_orders ADD COLUMN error_code VARCHAR(50);

COMMIT;

BEGIN TRANSACTION;

-- Add error_message if missing
ALTER TABLE payment_orders ADD COLUMN error_message TEXT;

COMMIT;

BEGIN TRANSACTION;

-- Add payment_method if missing
ALTER TABLE payment_orders ADD COLUMN payment_method VARCHAR(50);

COMMIT;

BEGIN TRANSACTION;

-- Add paid_at if missing
ALTER TABLE payment_orders ADD COLUMN paid_at TIMESTAMP;

COMMIT;

BEGIN TRANSACTION;

-- Add expires_at if missing
ALTER TABLE payment_orders ADD COLUMN expires_at TIMESTAMP;

COMMIT;

BEGIN TRANSACTION;

-- Add updated_at if missing
ALTER TABLE payment_orders ADD COLUMN updated_at TIMESTAMP;

COMMIT;

-- ================================================
-- CREATE INDEXES ON PAYMENT_ORDERS
-- ================================================

-- Index on payment_id for quick lookups
CREATE INDEX IF NOT EXISTS idx_orders_payment_id 
    ON payment_orders(payment_id);

-- Index on created_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_orders_created_at 
    ON payment_orders(created_at DESC);

-- Index on status for filtering
CREATE INDEX IF NOT EXISTS idx_orders_status 
    ON payment_orders(status);

-- Index on phone for user lookups
CREATE INDEX IF NOT EXISTS idx_orders_phone 
    ON payment_orders(phone);

-- Index on razorpay_order_id for webhook processing
CREATE INDEX IF NOT EXISTS idx_orders_razorpay_order_id 
    ON payment_orders(razorpay_order_id);

-- ================================================
-- VERIFICATION QUERIES
-- ================================================

-- Check webhook_events table was created
SELECT 'webhook_events table' as table_name, COUNT(*) as row_count 
FROM webhook_events;

-- Check payment_orders table structure
PRAGMA table_info(payment_orders);

-- Show all tables
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- Show all indexes
SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;

-- ================================================
-- SUCCESS MESSAGE
-- ================================================

SELECT '✅ Migration 001 completed successfully!' as status;
SELECT '✅ webhook_events table created' as message;
SELECT '✅ Indexes created for performance' as message;
SELECT '✅ payment_orders table updated with new columns' as message;
SELECT '✅ System ready for idempotent webhook processing' as message;