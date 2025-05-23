# Git Hooks for Clean Architecture Enforcement
#
# This script installs Git hooks that enforce our clean architecture
# guidelines and commit message standards.
#
# Usage: python install_git_hooks.py

import os
import stat
import shutil
from pathlib import Path

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
GIT_HOOKS_DIR = os.path.join(ROOT_DIR, '.git', 'hooks')

# Ensure git hooks directory exists
if not os.path.exists(GIT_HOOKS_DIR):
    print(f"Git hooks directory not found: {GIT_HOOKS_DIR}")
    print("Make sure this is a Git repository.")
    exit(1)

# Pre-commit hook to validate architecture compliance
PRE_COMMIT_HOOK = """#!/usr/bin/env python
import os
import re
import sys
import subprocess

# Get staged files
staged_files = subprocess.check_output(['git', 'diff', '--cached', '--name-only']).decode('utf-8').splitlines()

# Architecture validation patterns
domain_imports_infra = re.compile(r'^from .*\.infrastructure import')
domain_imports_app = re.compile(r'^from .*\.application import')
application_imports_presentation = re.compile(r'^from .*\.presentation import')

# Define modules and their layers
modules = ['core_banking', 'payments', 'treasury', 'digital_channels', 
           'crm', 'risk_compliance', 'hr_erp', 'security']
layers = ['domain', 'application', 'infrastructure', 'presentation']

errors = []

# Check files for clean architecture violations
for file in staged_files:
    if not file.endswith('.py'):
        continue
        
    # Determine which module and layer the file belongs to
    file_module = None
    file_layer = None
    
    for module in modules:
        if module in file:
            file_module = module
            break
    
    if not file_module:
        continue
        
    for layer in layers:
        if f"/{layer}/" in file or f"\\{layer}\\" in file:
            file_layer = layer
            break
    
    if not file_layer:
        continue
        
    # Check for architecture violations
    with open(file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line_number = i + 1
            
            # Domain layer should not import from other layers
            if file_layer == 'domain':
                if domain_imports_infra.search(line) or domain_imports_app.search(line) or 'from presentation import' in line:
                    errors.append(f"{file}:{line_number} - Domain layer cannot import from other layers: '{line.strip()}'")
            
            # Application layer should not import from presentation or infrastructure
            elif file_layer == 'application':
                if application_imports_presentation.search(line) or 'from presentation import' in line:
                    errors.append(f"{file}:{line_number} - Application layer cannot import from presentation layer: '{line.strip()}'")

# Report errors
if errors:
    print("❌ Clean Architecture violations found:")
    for error in errors:
        print(f"  - {error}")
    print("Commit aborted. Please fix the above violations.")
    sys.exit(1)
else:
    print("✅ Clean Architecture validation passed.")
    sys.exit(0)
"""

# Commit message hook to enforce standards
COMMIT_MSG_HOOK = """#!/usr/bin/env python
import sys
import re

# Get the commit message file
commit_msg_file = sys.argv[1]

# Read the commit message
with open(commit_msg_file, 'r') as f:
    commit_msg = f.read()

# Define the pattern for valid commit messages
# Format: [module] type: subject
pattern = r'^\[([a-zA-Z_-]+)\] (feat|fix|docs|style|refactor|test|chore): .{5,}'

# Check if the commit message matches the pattern
if not re.match(pattern, commit_msg):
    print("❌ Invalid commit message format.")
    print("Commit messages must follow the pattern: [module] type: subject")
    print("  - module: The module being changed (e.g. core_banking, payments)")
    print("  - type: One of: feat, fix, docs, style, refactor, test, chore")
    print("  - subject: A short description of the change (at least 5 characters)")
    print("\nExamples:")
    print("  [core_banking] feat: add new account creation API")
    print("  [payments] fix: resolve transaction timeout issue")
    print("  [security] refactor: improve authentication flow")
    sys.exit(1)
else:
    print("✅ Commit message format is valid.")
    sys.exit(0)
"""

def create_hook(path, content):
    """Create a git hook file with the given content"""
    with open(path, 'w') as f:
        f.write(content)
    
    # Make it executable
    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
    print(f"Created hook: {path}")

def install_hooks():
    """Install all git hooks"""
    # Pre-commit hook
    pre_commit_path = os.path.join(GIT_HOOKS_DIR, 'pre-commit')
    create_hook(pre_commit_path, PRE_COMMIT_HOOK)
    
    # Commit-msg hook
    commit_msg_path = os.path.join(GIT_HOOKS_DIR, 'commit-msg')
    create_hook(commit_msg_path, COMMIT_MSG_HOOK)
    
    print("\nGit hooks installed successfully!")
    print("Clean Architecture guidelines will now be enforced during commits.")
    print("\nCommit message format: [module] type: subject")
    print("  Example: [core_banking] feat: add new account creation API")

if __name__ == "__main__":
    install_hooks()
