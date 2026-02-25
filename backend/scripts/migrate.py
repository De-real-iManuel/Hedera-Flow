#!/usr/bin/env python3
"""
Database migration management script for Hedera Flow MVP

Usage:
    python scripts/migrate.py upgrade head    # Apply all migrations
    python scripts/migrate.py downgrade -1    # Rollback one migration
    python scripts/migrate.py current         # Show current revision
    python scripts/migrate.py history         # Show migration history
    python scripts/migrate.py revision -m "description"  # Create new migration
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alembic.config import Config
from alembic import command


def get_alembic_config():
    """Get Alembic configuration"""
    # Get the backend directory path
    backend_dir = Path(__file__).resolve().parent.parent
    alembic_ini = backend_dir / "alembic.ini"
    
    if not alembic_ini.exists():
        print(f"Error: alembic.ini not found at {alembic_ini}")
        sys.exit(1)
    
    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(backend_dir / "migrations"))
    
    return config


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    config = get_alembic_config()
    cmd = sys.argv[1]
    
    try:
        if cmd == "upgrade":
            revision = sys.argv[2] if len(sys.argv) > 2 else "head"
            print(f"Upgrading database to revision: {revision}")
            command.upgrade(config, revision)
            print("✓ Migration completed successfully")
            
        elif cmd == "downgrade":
            revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
            print(f"Downgrading database to revision: {revision}")
            command.downgrade(config, revision)
            print("✓ Rollback completed successfully")
            
        elif cmd == "current":
            print("Current database revision:")
            command.current(config)
            
        elif cmd == "history":
            print("Migration history:")
            command.history(config)
            
        elif cmd == "revision":
            if "-m" not in sys.argv:
                print("Error: -m flag required for revision message")
                print("Usage: python scripts/migrate.py revision -m 'description'")
                sys.exit(1)
            
            message_idx = sys.argv.index("-m") + 1
            if message_idx >= len(sys.argv):
                print("Error: No message provided after -m flag")
                sys.exit(1)
            
            message = sys.argv[message_idx]
            print(f"Creating new migration: {message}")
            command.revision(config, message=message, autogenerate=False)
            print("✓ Migration file created successfully")
            
        elif cmd == "stamp":
            revision = sys.argv[2] if len(sys.argv) > 2 else "head"
            print(f"Stamping database with revision: {revision}")
            command.stamp(config, revision)
            print("✓ Database stamped successfully")
            
        else:
            print(f"Unknown command: {cmd}")
            print(__doc__)
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
