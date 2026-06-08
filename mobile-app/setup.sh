#!/bin/bash

# Mobile App Setup Script
# AI Chief of Staff - React Native App

set -e

echo "🚀 Setting up AI Chief of Staff Mobile App..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

echo "✅ Node.js $(node --version) found"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed."
    exit 1
fi

echo "✅ npm $(npm --version) found"
echo ""

# Install dependencies
echo "📦 Installing npm dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"
echo ""

# iOS setup (only on macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Setting up iOS..."

    if ! command -v pod &> /dev/null; then
        echo "⚠️  CocoaPods not found. Installing..."
        sudo gem install cocoapods
    fi

    cd ios
    echo "📦 Installing CocoaPods dependencies..."
    pod install
    cd ..

    echo "✅ iOS setup complete"
else
    echo "⏭️  Skipping iOS setup (not on macOS)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Make sure backend is running: docker-compose up"
echo "  2. For real devices: Update API URL in src/api/client.ts"
echo "  3. Run the app:"
echo "     - iOS: npm run ios"
echo "     - Android: npm run android"
echo ""
echo "📖 Read QUICKSTART.md for detailed instructions"
echo ""
