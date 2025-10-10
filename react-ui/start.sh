#!/bin/bash

# Elastic News React UI Startup Script

echo "🚀 Starting Elastic News React UI..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check if agents are running
echo "🔍 Checking if news agents are running..."
if ! curl -s http://localhost:8080 > /dev/null; then
    echo "⚠️  News Chief (port 8080) is not responding."
    echo "   Please start the agents first: ./start_newsroom.sh"
    echo ""
fi

# Start the React app
echo "🌐 Starting React development server on port 3001..."
echo "   Open http://localhost:3001 in your browser"
echo ""

PORT=3001 npm start
