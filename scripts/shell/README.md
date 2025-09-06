# Shell Scripts

This directory contains shell-based system operation and automation scripts for the Docsmait system.

## Scripts Overview

### `comprehensive_backup.sh`
Comprehensive system backup script that creates complete backups of database and knowledge base.

### `manage_system.sh`
Unified system management tool providing interface for common administrative tasks.

### `reset_all_data.sh`
Complete data reset script - removes all data with safety confirmations and prompts.

### `restore.sh`
System restore tool for recovering the system from backup files.

### `system_health.sh`
System health monitoring script that checks and reports on system status.

### `template_manager.sh`
Template management utility for handling document templates and template operations.

## Requirements

All shell scripts require:
- Bash shell (4.0+)
- Docker and Docker Compose
- Appropriate system permissions
- Network access to services

## Usage

Scripts can be run directly:

```bash
# Make executable if needed
chmod +x scripts/shell/[script_name].sh

# Run from project root or scripts directory
./scripts/shell/[script_name].sh [options]
```

## Safety Features

Shell scripts include:
- Interactive confirmations for destructive operations
- Service availability checks
- Backup verification
- Error handling and rollback capabilities
- Progress indicators and status reporting

## Docker Integration

Most scripts are designed to work with the Docker-based Docsmait deployment and include:
- Container status checking
- Service restart capabilities
- Volume management
- Network connectivity verification

For detailed usage instructions, see the main scripts README.md or run any script with `--help` or `-h`.