def log_info(msg):
    print(f"\033[94m[INFO] {msg}\033[0m")

def log_success(msg):
    print(f"\033[92m[SUCCESS] {msg}\033[0m")

def log_warning(msg):
    print(f"\033[93m[WARNING] {msg}\033[0m")

def log_error(msg):
    print(f"\033[91m[ERROR] {msg}\033[0m")

def log_debug(msg, enabled=False):
    if enabled:
        print(f"\033[90m[DEBUG] {msg}\033[0m")
