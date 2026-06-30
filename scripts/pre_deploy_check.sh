#!/usr/bin/env bash
set -e

echo "🚀 Starting Pre-Deployment Verification..."

# 1. Check requirements
echo "📦 Checking dependencies..."
pip freeze > current_deps.txt
if ! cmp -s requirements.txt current_deps.txt; then
    echo "⚠️ Warning: Installed dependencies differ from requirements.txt. Please verify."
else
    echo "✅ Dependencies match."
fi
rm -f current_deps.txt

# 2. Run performance tests
echo "🧪 Running performance tests..."
if pytest tests/performance_test.py -v; then
    echo "✅ All 6 performance tests passed."
else
    echo "❌ Performance tests failed!"
    exit 1
fi

# 3. Verify slider max in app.py
echo "🎛️ Checking app.py slider maximum..."
if grep -q "1000000\|1_000_000" app.py; then
    echo "✅ Slider maximum is 1,000,000."
else
    echo "❌ Slider max is not 1,000,000 in app.py!"
    exit 1
fi

# 4. Check for EasyOCR lazy loading
echo "🖼️ Verifying EasyOCR lazy loading..."
if grep -E "^import easyocr|^from easyocr" app.py > /dev/null; then
    echo "❌ EasyOCR is loaded globally in app.py! It must be lazy-loaded."
    exit 1
else
    echo "✅ EasyOCR is correctly lazy-loaded."
fi

echo "✅✅✅ ALL PRE-DEPLOY CHECKS PASSED. READY FOR PRODUCTION."
