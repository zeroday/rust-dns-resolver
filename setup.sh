#!/bin/bash

# Exit on any error
set -e

echo "Starting setup process..."

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# Install required packages
echo "Installing required packages..."
sudo apt-get install -y git curl build-essential

# Install Rust using rustup
echo "Installing Rust..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env

# Clone the repository
echo "Cloning rust-dns-resolver repository..."
git clone git@github.com:zeroday/rust-dns-resolver.git

# Change into the project directory
echo "Changing to project directory..."
cd rust-dns-resolver

# Build the project
echo "Building the Rust project..."
cargo build --release

# Make the script executable
chmod +x setup.sh

echo "Setup completed successfully!" 