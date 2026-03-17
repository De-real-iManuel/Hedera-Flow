import sys
import traceback

sys.path.insert(0, '.')

try:
    print("Attempting to import test module...")
    import tests.test_meters_all_regions as test_module
    print("Import successful!")
    print("Module attributes:", [x for x in dir(test_module) if not x.startswith('_')])
except Exception as e:
    print(f"Import failed with error: {e}")
    traceback.print_exc()
