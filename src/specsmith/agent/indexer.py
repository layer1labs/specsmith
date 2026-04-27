import os
import json
import glob
import subprocess
from pathlib import Path

def generate_index(cwd: str = None):
    """Generate repository index into .repo-index/"""
    if cwd is None:
        cwd = os.getcwd()
        
    index_dir = Path(cwd) / ".repo-index"
    index_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating repository context index...")
    
    # 1. files.json
    try:
        # Try ripgrep first
        result = subprocess.run(
            ["rg", "--files"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        files = result.stdout.splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to glob
        print("rg not found or failed, falling back to glob...")
        files = glob.glob("**/*", recursive=True, root_dir=cwd)
        files = [f for f in files if os.path.isfile(os.path.join(cwd, f))]
        
    files_path = index_dir / "files.json"
    files_path.write_text(json.dumps(files, indent=2))
    print(f"Indexed {len(files)} files into files.json")
    
    # 2. symbols.json (via ctags)
    try:
        subprocess.run(
            ["ctags", "-R", "-f", str(index_dir / "tags"), "."],
            cwd=cwd,
            capture_output=True,
            check=True
        )
        print("Generated ctags index.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ctags not found or failed, skipping symbols index.")
        
    # 3. test_commands.json (pytest collect-only)
    try:
        result = subprocess.run(
            ["pytest", "--collect-only", "-q"],
            cwd=cwd,
            capture_output=True,
            text=True
        )
        test_commands = result.stdout.splitlines()
        tests_path = index_dir / "test_commands.json"
        tests_path.write_text(json.dumps(test_commands, indent=2))
        print("Indexed tests into test_commands.json")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("pytest not found or failed, skipping test collection.")

    # 4. architecture.md and conventions.md stubs if they don't exist
    arch_path = index_dir / "architecture.md"
    if not arch_path.exists():
        arch_path.write_text("# Architecture\n\nRun `/ask architecture` to populate this file.")
        
    conv_path = index_dir / "conventions.md"
    if not conv_path.exists():
        conv_path.write_text("# Conventions\n\nRun `/ask conventions` to populate this file.")
        
    print("Context index generation complete.")

if __name__ == "__main__":
    generate_index()
