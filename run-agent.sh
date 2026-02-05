#!/usr/bin/env bash
cd "$(dirname "$0")"
#while true; do
    python -m agent.driver
    echo "Agent exited ($?)." # Restarting in 5 seconds..."
#    sleep 5
#done
