#!/bin/bash

# Start API server and wait for initialization
python3 api_server.py &

# Wait for API to become available
echo "Waiting for API server to start..."
MAX_WAIT=10
for ((i=1; i<=$MAX_WAIT; i++)); do
    if curl -s http://localhost:5000/api/health >/dev/null; then
        echo "API server ready"
        break
    fi
    echo "Waiting... ($i/$MAX_WAIT)"
    sleep 1
done

# Start Streamlit app with explicit config
echo "Starting Streamlit..."
streamlit run app.py \
    --server.headless true \
    --server.runOnSave true \
    --server.enableCORS true

# Cleanup on exit
kill %1