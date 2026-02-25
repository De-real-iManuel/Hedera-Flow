"""
Master Seed Script - All Utilities (USA, India, Brazil, Spain)
Runs all utility seeding scripts in sequence
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

scripts_dir = os.path.dirname(os.path.abspath(__file__))
usa = load_module('seed_usa_utilities', os.path.join(scripts_dir, 'seed_usa_utilities.py'))
india = load_module('seed_india_utilities', os.path.join(scripts_dir, 'seed_india_utilities.py'))
brazil = load_module('seed_brazil_utilities', os.path.join(scripts_dir, 'seed_brazil_utilities.py'))
spain = load_module('seed_spain_utilities', os.path.join(scripts_dir, 'seed_spain_utilities.py'))

def seed_all_utilities():
    print("\n" + "=" * 70)
    print("SEEDING ALL UTILITIES FOR USA, INDIA, BRAZIL, SPAIN")
    print("=" * 70 + "\n")
    
    try:
        usa.seed_usa_utilities()
        print()
        india.seed_india_utilities()
        print()
        brazil.seed_brazil_utilities()
        print()
        spain.seed_spain_utilities()
        
        print("\n" + "=" * 70)
        print("✓ ALL UTILITIES SEEDED SUCCESSFULLY!")
        print("=" * 70)
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        raise

if __name__ == "__main__":
    seed_all_utilities()
