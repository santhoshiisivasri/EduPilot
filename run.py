"""
EduPilot – Application Entry Point
Run with: python run.py
"""
import os
import sys

# Force UTF-8 output on Windows to avoid emoji encoding errors
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    print("=" * 52)
    print("  EduPilot - AI-Powered Learning Platform")
    print("  Powered by IBM Watsonx.ai Granite Models")
    print("=" * 52)
    print(f"  Server : http://localhost:{port}")
    print(f"  Debug  : {debug}")
    print("=" * 52)
    app.run(host='0.0.0.0', port=port, debug=debug)
