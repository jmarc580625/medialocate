# GPG Key Setup Guide for Commit Signing

## Prerequisites
- GnuPG installed
- GitHub account
- Git configured with your GitHub email

## Step-by-Step Guide

### 1. Install GPG Tools
```bash
# Windows (using Chocolatey)
choco install gnupg

# macOS (using Homebrew)
brew install gnupg

# Linux (Ubuntu/Debian)
sudo apt-get install gnupg
```

### 2. Generate GPG Key
```bash
# Generate a new GPG key
gpg --full-generate-key

# Choose these options:
# - Key type: RSA and RSA (default)
# - Key size: 4096 bits
# - Expiration: 1-2 years (recommended)
# - Real name: Your GitHub username
# - Email: Email associated with GitHub
# - Passphrase: Use a strong, unique passphrase
```

### 3. List and Verify GPG Key
```bash
# List GPG keys
gpg --list-secret-keys --keyid-format=long

# Example output:
# sec   rsa4096/ABCD1234EFGH5678 2024-02-15 [SC]
#       LONG_KEY_FINGERPRINT
# uid                 Your Name <your.email@example.com>
```

### 4. Export GPG Public Key
```bash
# Export public key (replace ABCD1234EFGH5678 with your key ID)
gpg --armor --export ABCD1234EFGH5678 > gpg_public_key.asc
```

### 5. Configure Git to Use GPG Key
```bash
# Set Git to use your GPG key
git config --global user.signingkey ABCD1234EFGH5678
git config --global commit.gpgsign true
```

### 6. Add GPG Key to GitHub
1. Copy the contents of `gpg_public_key.asc`
2. Go to GitHub Settings > SSH and GPG Keys
3. Click "New GPG Key"
4. Paste the public key

### 7. Test Commit Signing
```bash
# Make a test commit
git checkout -b test-signing
echo "Test commit signing" > test.txt
git add test.txt
git commit -S -m "Test commit signature"

# Verify the commit is signed
git log --show-signature
```

### 8. Backup GPG Key (CRITICAL)
```bash
# Export private and public keys
gpg --export-secret-keys > private_gpg_key_backup.asc
gpg --export > public_gpg_key_backup.asc

# Store backups in secure, encrypted storage
```

## Troubleshooting
- Ensure your Git email matches the GPG key email
- Check GPG agent is running
- Verify GitHub recognizes the GPG key

## Security Recommendations
- Use a strong passphrase
- Store private key backup in encrypted storage
- Consider using a hardware security key
- Rotate keys periodically (every 1-2 years)
