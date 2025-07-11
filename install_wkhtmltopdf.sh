#!/bin/bash

# Quick installer for wkhtmltopdf on Ubuntu/Debian systems
# This script installs wkhtmltopdf with all required dependencies

echo "🚀 Installing wkhtmltopdf for PDF generation..."

# Update package list
sudo apt-get update

# Install wkhtmltopdf and required dependencies
sudo apt-get install -y \
    wkhtmltopdf \
    xvfb \
    fontconfig \
    libxrender1 \
    libfontconfig1 \
    libx11-6 \
    libjpeg62 \
    libxtst6

# Verify installation
if command -v wkhtmltopdf &> /dev/null; then
    echo "✅ wkhtmltopdf installed successfully!"
    echo "Version: $(wkhtmltopdf --version)"
    
    # Test PDF generation
    echo "🧪 Testing PDF generation..."
    echo "<html><body><h1>Test PDF</h1><p>This is a test document.</p></body></html>" | wkhtmltopdf - test_output.pdf
    
    if [ -f "test_output.pdf" ]; then
        echo "✅ PDF generation test successful!"
        rm test_output.pdf
    else
        echo "❌ PDF generation test failed"
        exit 1
    fi
else
    echo "❌ wkhtmltopdf installation failed"
    exit 1
fi

echo "🎉 Setup complete! You can now use the HTML to PDF API."
