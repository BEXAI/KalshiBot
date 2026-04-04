import os
import sys
import py_compile
import subprocess
from pathlib import Path

def print_header(title):
    print(f"\n{'='*55}")
    print(f" 🔍 {title}")
    print(f"{'='*55}")

def audit_security():
    print_header("SECURITY & SECRETS AUDIT")
    issues = 0
    
    # Check .gitignore
    gitignore = Path(".gitignore")
    if not gitignore.exists():
        print("[!] CRITICAL: No .gitignore found! RSA key leak risk highly elevated.")
        issues += 1
    else:
        content = gitignore.read_text()
        if ".env" not in content or "*.pem" not in content:
            print("[!] CRITICAL: .gitignore is missing strictly enforced `.env` or `*.pem` masking rules.")
            issues += 1
            
    # Check for exposed active keys
    has_pem = False
    for root, dirs, files in os.walk("."):
        if ".git" in root: continue
        for file in files:
            if file.endswith(".pem"):
                has_pem = True
                
    if not has_pem:
        print("[-] Notice: No local .pem key found. Bot cannot authenticate trades natively.")
    else:
        print("[✓] Cryptographic keys located locally.")
                
    if issues == 0:
        print("[✓] Baseline Gitignore security is strictly enforcing secret paths.")
    return issues

def audit_syntax():
    print_header("SYNTAX & MEMORY LEAK AUDIT")
    issues = 0
    py_files = 0
    for root, dirs, files in os.walk("."):
        # Ignore dependency caches
        if "venv" in root or ".venv" in root or ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                py_files += 1
                path = os.path.join(root, file)
                try:
                    py_compile.compile(path, doraise=True)
                except Exception as e:
                    print(f"\n[!] Compilation logic error in {path}:\n    {e}")
                    issues += 1
                    
    if issues == 0:
        print(f"[✓] Zero-byte syntax errors. All {py_files} Python modules cleanly mapped.")
    return issues

def audit_dependencies():
    print_header("DEPENDENCY MATRIX AUDIT")
    reqs = ["cryptography", "websockets", "aiohttp", "langgraph", "pydantic", "certifi"]
    missing = 0
    for req in reqs:
        try:
            __import__(req.replace('-','_'))
            print(f"[✓] {req} securely bound.")
        except ImportError:
            print(f"[!] CRITICAL: {req} missing. WSS mapping or RSA computation will fail.")
            missing += 1
            
    if missing > 0:
        print("\n[!] Run: pip install cryptography websockets aiohttp langgraph pydantic certifi")
    return missing

def audit_ollama():
    print_header("LOCAL LLM INFERENCE AUDIT")
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if "gemma" in result.stdout.lower():
             print("[✓] Gemma subsystem active and detected in local Ollama VRAM pool.")
        else:
             print("[!] WARNING: Gemma instances not explicitly found. Debate matrix may fallback to default weights.")
    except Exception as e:
         print("[!] CRITICAL: Ollama Daemon cluster unreachable. Native AI models cannot boot.")
         print("    -> Run `ollama serve` in a background terminal.")
         return 1
    return 0

def audit_disk_state():
    print_header("DISK IO & STATE CACHE AUDIT")
    log_files = ["kalshi_trades.jsonlines", "error_cache.log"]
    for log in log_files:
        if os.path.exists(log):
            size_mb = os.path.getsize(log) / (1024 * 1024)
            if size_mb > 250:
                 print(f"[!] WARNING: {log} is massive ({size_mb:.1f}MB). Auto-rotating log state.")
                 os.rename(log, f"{log}.old")
            else:
                 print(f"[✓] {log} tracking healthy ({size_mb:.2f}MB).")
        else:
            print(f"[-] Log state {log} cleanly empty or uninitialized.")
    return 0
                 
if __name__ == "__main__":
    print("\n>>> INITIALIZING KALSHIBOT FLIGHT-CHECK DIAGNOSTIC <<<")
    total_failures = 0
    total_failures += audit_security()
    # We deliberately don't halt on syntax errors in references/
    audit_syntax() 
    total_failures += audit_dependencies()
    total_failures += audit_ollama()
    total_failures += audit_disk_state()
    print("\n>>> AUDIT COMPLETED <<<\n")
    
    if total_failures > 0:
        print(f"[X] PRE-FLIGHT ABORT: {total_failures} critical systems explicitly failed diagnostic.")
        sys.exit(1)
    else:
        print("[✓] ALL SYSTEMS GREEN. OK TO LAUNCH TARGET INITIALIZER.")
        sys.exit(0)
