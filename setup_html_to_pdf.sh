#!/bin/bash

# Setup script for HTML to PDF API
# This script installs system dependencies required for PDF generation

echo "🚀 Setting up HTML to PDF API dependencies..."

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            echo "debian"
        elif [ -f /etc/redhat-release ]; then
            echo "redhat"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Install wkhtmltopdf based on OS
install_wkhtmltopdf() {
    local os=$(detect_os)
    
    echo "🔍 Detected OS: $os"
    
    case $os in
        "debian")
            echo "📦 Installing wkhtmltopdf for Debian/Ubuntu..."
            sudo apt-get update
            sudo apt-get install -y wkhtmltopdf
            ;;
        "redhat")
            echo "📦 Installing wkhtmltopdf for RedHat/CentOS..."
            sudo yum install -y wkhtmltopdf || sudo dnf install -y wkhtmltopdf
            ;;
        "macos")
            echo "📦 Installing wkhtmltopdf for macOS..."
            if command -v brew &> /dev/null; then
                brew install wkhtmltopdf
            else
                echo "❌ Homebrew not found. Please install Homebrew first or install wkhtmltopdf manually."
                echo "   Download from: https://wkhtmltopdf.org/downloads.html"
                exit 1
            fi
            ;;
        "windows")
            echo "❌ Windows detected. Please install wkhtmltopdf manually."
            echo "   Download from: https://wkhtmltopdf.org/downloads.html"
            echo "   Make sure to add it to your PATH."
            exit 1
            ;;
        *)
            echo "❌ Unknown OS. Please install wkhtmltopdf manually."
            echo "   Download from: https://wkhtmltopdf.org/downloads.html"
            exit 1
            ;;
    esac
}

# Check if wkhtmltopdf is already installed
check_wkhtmltopdf() {
    if command -v wkhtmltopdf &> /dev/null; then
        echo "✅ wkhtmltopdf is already installed"
        wkhtmltopdf --version
        return 0
    else
        echo "❌ wkhtmltopdf not found"
        return 1
    fi
}

# Install Python dependencies
install_python_deps() {
    echo "🐍 Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        echo "❌ requirements.txt not found"
        exit 1
    fi
}

# Test PDF generation
test_pdf_generation() {
    echo "🧪 Testing PDF generation..."
    
    python3 -c "
import pdfkit
try:
    pdf = pdfkit.from_string('<h1>Test</h1>', False)
    print('✅ PDF generation test successful')
except Exception as e:
    print(f'❌ PDF generation test failed: {e}')
    exit(1)
"
}

# Main setup process
main() {
    echo "Starting setup for HTML to PDF API..."
    echo "======================================"
    
    # Check if wkhtmltopdf is installed, install if not
    if ! check_wkhtmltopdf; then
        install_wkhtmltopdf
        
        # Verify installation
        if ! check_wkhtmltopdf; then
            echo "❌ Failed to install wkhtmltopdf"
            exit 1
        fi
    fi
    
    # Install Python dependencies
    install_python_deps
    
    # Test PDF generation
    test_pdf_generation
    
    echo ""
    echo "✅ Setup completed successfully!"
    echo ""
    echo "🎯 Next steps:"
    echo "1. Make sure your database is running"
    echo "2. Configure your .env file with database and S3 credentials"
    echo "3. Start the server with: python server.py"
    echo "4. Test the API with: python test_html_to_pdf.py"
}

# Run main function
main
