import signal
import sys
from typing import Callable

def setup_signal_handlers(logger: Callable[[str], None] = print):
    """
    Sets up signal handlers to prevent accidental closure via Ctrl+Z (SIGTSTP).
    Ctrl+C (SIGINT) is typically handled by Textual's event loop as a key press, 
    but we catch the system signal just in case.
    """
    
    def handle_sigz(signum, frame):
        logger("Ctrl+Z (Suspend) is disabled. Please use 'q' to quit.")

    # Validate if we are in the main thread (signals only work there)
    try:
        # Ignore SIGTSTP (Ctrl+Z)
        signal.signal(signal.SIGTSTP, handle_sigz)
    except Exception as e:
        logger(f"Could not setup signal handlers: {e}")
