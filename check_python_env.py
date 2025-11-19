import sys
import os

print("=" * 60)
print("PYTHON ENVIRONMENT INFO")
print("=" * 60)
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python path:")
for p in sys.path:
    print(f"  - {p}")
print()
print("=" * 60)
print("INSTALLED PACKAGES (openai)")
print("=" * 60)

try:
    import openai
    print(f"✅ openai module found: {openai.__file__}")
    print(f"   Version: {openai.__version__}")
except ImportError as e:
    print(f"❌ openai not found: {e}")

print()
print("=" * 60)
print("CHECKING pip list for openai")
print("=" * 60)
os.system(f'"{sys.executable}" -m pip list | findstr openai')
