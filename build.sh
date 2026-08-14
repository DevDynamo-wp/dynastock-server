#!/bin/bash
# Dynastock-server Build Script

set -e  # Exit on any error

echo "=========================================="
echo "Dynastock-server Build Process"
echo "=========================================="

# Step 1: Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Step 2: Collect static files
echo ""
echo "📁 Collecting static files..."
python manage.py collectstatic --no-input || echo "⚠️  collectstatic skipped (no static files needed)"

# Step 3: Run migrations
echo ""
echo "🗄️  Running database migrations..."
python manage.py migrate

# Step 4: Load fixtures
echo ""
echo "📋 Loading initial data (fixtures)..."
python manage.py loaddata apps/subscriptions/fixtures/subscription_plans.json

echo ""
echo "=========================================="
echo "✅ Build completed successfully!"
echo "=========================================="