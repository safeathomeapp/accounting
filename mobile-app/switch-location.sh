#!/bin/bash

################################################################################
# Switch Location Script for Mac/Linux
#
# This script makes it easy to switch between Location 1 and Location 2
#
# Usage:
#   chmod +x switch-location.sh  (only needed once)
#   ./switch-location.sh location1
#   ./switch-location.sh location2
#
# Examples:
#   ./switch-location.sh location1  -> Uses 192.168.1.143
#   ./switch-location.sh location2  -> Uses 192.168.0.37
################################################################################

# Check if argument provided
if [ -z "$1" ]; then
    echo ""
    echo "============================================================================"
    echo " Environment Location Switcher"
    echo "============================================================================"
    echo ""
    echo "Usage: ./switch-location.sh [location1 or location2]"
    echo ""
    echo "Examples:"
    echo "  ./switch-location.sh location1  - Switch to Location 1 (192.168.1.143)"
    echo "  ./switch-location.sh location2  - Switch to Location 2 (192.168.0.37)"
    echo ""
    echo "Current .env.local:"
    if [ -f ".env.local" ]; then
        grep "^API_BASE_URL" .env.local
    else
        echo "  [Not set yet]"
    fi
    echo ""
    exit 0
fi

# Get the location argument
LOCATION=$1

# Validate and switch
case "$LOCATION" in
    location1)
        echo "Switching to Location 1 (192.168.1.143)..."
        cp ".env.location1" ".env.local"
        echo ""
        echo "SUCCESS: Switched to Location 1"
        echo "API_BASE_URL=http://192.168.1.143:8000/api/mobile"
        echo ""
        echo "Next steps:"
        echo "  1. Stop npm start (Ctrl+C)"
        echo "  2. Run: npm start"
        echo ""
        ;;
    location2)
        echo "Switching to Location 2 (192.168.0.37)..."
        cp ".env.location2" ".env.local"
        echo ""
        echo "SUCCESS: Switched to Location 2"
        echo "API_BASE_URL=http://192.168.0.37:8000/api/mobile"
        echo ""
        echo "Next steps:"
        echo "  1. Stop npm start (Ctrl+C)"
        echo "  2. Run: npm start"
        echo ""
        ;;
    *)
        echo ""
        echo "ERROR: Invalid location \"$LOCATION\""
        echo ""
        echo "Valid options:"
        echo "  location1 - Use 192.168.1.143"
        echo "  location2 - Use 192.168.0.37"
        echo ""
        echo "Example: ./switch-location.sh location1"
        echo ""
        exit 1
        ;;
esac
