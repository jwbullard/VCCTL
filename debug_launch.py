#!/usr/bin/env python3

import sys
import os
import signal

# Add the src directory to the Python path
sys.path.insert(0, 'src')

def signal_handler(signum, frame):
    print(f"\n⚠️  Received signal {signum}")
    print("🔍 Debug info:")
    import traceback
    traceback.print_stack(frame)
    sys.exit(1)

# Set up signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

try:
    print("🚀 Starting VCCTL debug launch...")
    
    # Test imports first
    print("📦 Testing imports...")
    from app.application import VCCTLApplication
    print("✅ Application import successful")
    
    # Create application
    print("🏗️  Creating application...")
    app = VCCTLApplication()
    print("✅ Application created")
    
    # Override the activate method to add debug info
    original_activate = app._on_activate
    
    def debug_activate(app_ref):
        print("🎯 Application activation starting...")
        try:
            result = original_activate(app_ref)
            print("✅ Application activation completed")
            return result
        except Exception as e:
            print(f"❌ Activation failed: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    app._on_activate = debug_activate
    
    print("🏃 Running application...")
    # Start with a very short timeout to test
    import threading
    import time
    
    def timeout_killer():
        time.sleep(3)  # 3 second timeout
        print("\n⏰ Timeout reached - terminating for safety")
        os._exit(0)
    
    timeout_thread = threading.Thread(target=timeout_killer, daemon=True)
    timeout_thread.start()
    
    exit_code = app.run([])
    print(f"✅ Application exited normally with code: {exit_code}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)