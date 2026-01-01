# Security Guidelines

## Protecting Private Information

This repository is configured to automatically ignore sensitive files through `.gitignore`. 

### Files That Are Automatically Ignored:

1. **API Keys and Credentials**
   - `ai_assistant/API-KEY` - API keys for AI assistant
   - Any file containing `*api_key*`, `*API-KEY*`, etc.
   - `credentials.json`, `credentials.yaml`
   
2. **Environment Files**
   - `.env`, `.env.local`, `.env.production`, etc.
   - All files matching `*.env` pattern

3. **Private and Secret Files**
   - Any file with `secret` or `private` in the name
   - Files in `secrets/` or `private/` directories

4. **Certificate and Key Files**
   - `*.pem`, `*.key`, `*.cert`, `*.crt`, `*.p12`, `*.pfx`

5. **Configuration Files**
   - `config.json`, `settings.json`, `auth.json`
   - Cloud provider credential directories (`.aws/`, `.gcp/`, `.azure/`)

### Best Practices:

1. **Never commit sensitive data directly to the repository**
   
2. **Use environment variables for secrets**
   - Copy `.env.example` to `.env`
   - Fill in your actual values in `.env` (this file is ignored by git)
   
3. **Store API keys securely**
   - Place API keys in the `ai_assistant/API-KEY` file (ignored by git)
   - Or use environment variables instead
   
4. **Double-check before committing**
   - Run `git status` to ensure no sensitive files are being tracked
   - Review your changes with `git diff` before committing

5. **If you accidentally commit a secret**
   - Immediately revoke/rotate the compromised credentials
   - Contact a repository administrator
   - Consider using tools like `git-filter-repo` to remove the secret from history

### Using .env.example

The `.env.example` file provides a template for your environment variables. To use it:

```bash
cp .env.example .env
# Edit .env with your actual values
```

The `.env` file will be ignored by git and won't be committed.

## Reporting Security Issues

If you discover a security vulnerability, please report it privately to the repository maintainers.
