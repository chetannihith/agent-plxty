"""
Launch A2A Protocol Server
Run with: python run_a2a_server.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from resume_optimizer.a2a.server import start_server


def main():
    """Main entry point"""
    print("=" * 70)
    print("  RESUME OPTIMIZER A2A AGENT SERVER")
    print("=" * 70)
    print("\nEndpoints:")
    print("  Agent Card:      http://localhost:8000/.well-known/agent-card.json")
    print("  JSON-RPC:        http://localhost:8000/v1/message:send")
    print("  Tasks:           http://localhost:8000/v1/tasks")
    print("  Skills:          http://localhost:8000/v1/skills")
    print("  Health Check:    http://localhost:8000/health")
    print("  Documentation:   http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 70)
    print()
    
    # Start server
    start_server(
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable hot reload during development
    )


if __name__ == "__main__":
    main()
