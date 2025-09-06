# Python Scripts

This directory contains Python-based maintenance and management scripts for the Docsmait system.

## Scripts Overview

### `backup.py`
Database backup utility with comprehensive backup capabilities.

### `cleanup_system.py`
Comprehensive system cleanup for both database and knowledge base.

### `maintenance_tasks.py`
Routine maintenance tasks for optimal system performance.

### `reset_system.py`
Nuclear system reset - completely wipes all data and returns system to initial state.

### `restore.py`
System restore utility for recovering from backups.

## Requirements

All Python scripts require:
- Python 3.8+
- Backend application dependencies
- Database access permissions
- Proper environment configuration

## Usage

All scripts should be run from the project root directory:

```bash
# From project root
python scripts/python/[script_name].py [options]
```

## Safety Features

All scripts include:
- Dry-run mode for safe preview
- Confirmation prompts for destructive operations
- Automatic backup creation
- Detailed logging and error handling
- Rollback capabilities where applicable

For detailed usage instructions, see the main scripts README.md or run any script with `--help`.