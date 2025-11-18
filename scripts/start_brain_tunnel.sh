#!/bin/bash
# Start Brain SSH Tunnel
# Simple manual script to establish connection once per session

echo "🧠 Starting Brain SSH Tunnel..."
echo ""

# Kill any existing tunnels to avoid conflicts
existing=$(pgrep -f "ssh.*11434.*delta.cs.uwindsor.ca")
if [ -n "$existing" ]; then
  echo "⚠️  Existing tunnel found (PID: $existing)"
  echo "   Killing old tunnel..."
  pkill -f "ssh.*11434.*delta.cs.uwindsor.ca"
  sleep 2
fi

# Start new tunnel in background
echo "🔐 Connecting to delta.cs.uwindsor.ca..."
echo "   (You'll be prompted for your Delta password)"
echo ""

ssh -f -N -i ~/.ssh/id_ed25519 \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -L 11434:localhost:11434 \
  -L 11435:localhost:11435 \
  -L 11436:localhost:11436 \
  sharmas1@delta.cs.uwindsor.ca

# Check exit code
if [ $? -eq 0 ]; then
  echo ""
  echo "⏳ Waiting for tunnel to establish..."
  sleep 3
  
  # Test connection
  if nc -z localhost 11435 2>/dev/null; then
    echo ""
    echo "✅ Brain tunnel established successfully!"
    echo ""
    echo "   📡 Forwarded Ports:"
    echo "      • localhost:11434 → Fast Model (3B)"
    echo "      • localhost:11435 → Balanced Model (7B)"
    echo "      • localhost:11436 → Smart Model (14B)"
    echo ""
    echo "   🎯 Tunnel will stay active until you log out"
    echo "   💡 You can now use the Synth app!"
    echo ""
    
    # Show tunnel PID
    tunnel_pid=$(pgrep -f "ssh.*11434.*delta.cs.uwindsor.ca")
    echo "   🔧 Tunnel PID: $tunnel_pid"
    echo "   🛑 To stop: pkill -f 'ssh.*11434.*delta.cs.uwindsor.ca'"
    echo ""
  else
    echo ""
    echo "❌ Tunnel started but ports not accessible"
    echo "   Check if Ollama is running on Delta server"
    echo ""
    exit 1
  fi
else
  echo ""
  echo "❌ SSH connection failed"
  echo "   • Check your password"
  echo "   • Verify Delta server is reachable: ping delta.cs.uwindsor.ca"
  echo "   • Check your internet connection"
  echo ""
  exit 1
fi
