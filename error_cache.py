import json
import time
import traceback

class ErrorCache:
    """
    Centralized Error Caching utility. 
    Intercepts exceptions and dynamically dumps structural traces sideways to prevent main thread blocking!
    """
    _instance = None
    _log_file = "kalshi_error_dump.jsonlines"

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ErrorCache, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def record_error(self, component: str, exception: Exception, metadata: dict = None):
        """
        Securely parses and writes critical runtime errors without exploding the master loop.
        """
        error_payload = {
            "timestamp": time.time(),
            "component": component,
            "error_type": type(exception).__name__,
            "message": str(exception),
            "metadata": metadata or {},
            "traceback": "\\n".join(traceback.format_tb(exception.__traceback__)) if exception.__traceback__ else "None"
        }
        
        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(error_payload) + "\n")
            print(f"[ERROR CACHED] {component} safely logged to {self._log_file} -> {type(exception).__name__}: {str(exception)}")
        except Exception as fallback_e:
            # Absolute worst-case scenario: logging framework itself crashes 
            print(f"CRITICAL FALLBACK FAILURE IN ERROR CACHE: {fallback_e}")

# Instantiated Singleton to be shared globally without overhead
error_cache = ErrorCache()
