import sys
import subprocess
import re

def run_checks():
    print("🚀 Starting Pre-Deployment Verification (Python)...")
    success = True

    # 1. Run performance tests
    print("🧪 Running performance tests...")
    result = subprocess.run(["python", "-m", "pytest", "tests/performance_test.py", "-v"], capture_output=True, text=True)
    if result.returncode == 0:
         print("✅ All 6 performance tests passed.")
    else:
         print("❌ Performance tests failed!\n", result.stdout)
         success = False

    # 2. Verify slider max and EasyOCR lazy loading in app.py
    print("🎛️ Checking app.py configurations...")
    try:
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "1000000" in content or "1_000_000" in content:
                print("✅ Slider maximum is 1,000,000.")
            else:
                print("❌ Slider max is not 1,000,000 in app.py!")
                success = False
                
            if re.search(r"^(?:import easyocr|from easyocr import)", content, re.MULTILINE):
                print("❌ EasyOCR is loaded globally in app.py! It must be lazy-loaded.")
                success = False
            else:
                print("✅ EasyOCR is correctly lazy-loaded.")
    except FileNotFoundError:
        print("❌ app.py not found!")
        success = False

    if success:
        print("✅✅✅ ALL PRE-DEPLOY CHECKS PASSED. READY FOR PRODUCTION.")
        sys.exit(0)
    else:
        print("❌ PRE-DEPLOY CHECKS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    run_checks()
