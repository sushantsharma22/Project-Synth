#!/bin/bash
# Connect to Delta Brain with SSH tunneling
# This creates port forwards for all three Brain models

echo "🧠 Connecting to Delta Brain System"
echo "===================================="
echo ""
echo "Port Forwarding:"
echo "  11434 → 3B model (fast)"
echo "  11435 → 7B model (balanced)"
echo "  11436 → 14B model (smart)"
echo ""
echo "Keep this terminal open while using the Brain!"
echo ""

# SSH with port forwarding
ssh -L 11434:localhost:11434 \
    -L 11435:localhost:11435 \
    -L 11436:localhost:11436 \
    sharmas1@delta.cs.uwindsor.ca
