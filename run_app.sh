#!/bin/bash

echo "========================================="
echo "Clearing Streamlit cache..."
echo "========================================="

streamlit cache clear

echo ""
echo "========================================="
echo "Removing Streamlit session state..."
echo "========================================="

rm -rf ~/.streamlit

echo ""
echo "========================================="
echo "Starting Streamlit application..."
echo "========================================="

python -m streamlit run src/ui_app.py --server.maxUploadSize 1024