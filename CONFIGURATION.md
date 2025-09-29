# Configuration Setup Guide

This guide explains how to securely configure the Odia News Application backend with sensitive data like API keys and database credentials.

## 🔐 Security Overview

All sensitive data has been moved to a centralized configuration system to prevent accidental exposure of credentials in the codebase.

## 📁 Configuration Files

### 1. `functions/config.py`
- **Purpose**: Main configuration file that loads from environment variables
- **Security**: Contains no hardcoded secrets, only loads from environment
- **Status**: ✅ Safe to commit to version control

### 2. `functions/config_template.py`
- **Purpose**: Template file showing all required configuration variables
- **Usage**: Copy to `config_local.py` and fill in your actual values
- **Status**: ✅ Safe to commit to version control

### 3. `functions/config_local.py` (Create this file)
- **Purpose**: Your local configuration with actual sensitive values
- **Security**: ⚠️ **NEVER COMMIT THIS FILE** - It's in .gitignore
- **Usage**: Copy from `config_template.py` and fill in real values

## 🚀 Setup Instructions

### Step 1: Create Local Configuration
```bash
cd functions
cp config_template.py config_local.py
```

### Step 2: Fill in Your Values
Edit `config_local.py` and replace the placeholder values:

```python
# Database Configuration
DB_PASSWORD = "your_actual_database_password"
GEMINI_API_KEY = "your_actual_gemini_api_key"

# Optional: Firebase Configuration (if using advanced features)
FIREBASE_PROJECT_ID = "your_firebase_project_id"
FIREBASE_PRIVATE_KEY = "your_firebase_private_key"
FIREBASE_CLIENT_EMAIL = "your_firebase_client_email"
```

### Step 3: Environment Variables (Alternative)
Instead of `config_local.py`, you can set environment variables:

```bash
export DB_PASSWORD="your_database_password"
export GEMINI_API_KEY="your_gemini_api_key"
export DB_CONNECTION_NAME="your_connection_name"
export DB_USERNAME="your_username"
export DB_DATABASE="your_database_name"
```

## 🔧 Configuration Options

### Required Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `DB_PASSWORD` | PostgreSQL database password | `my_secure_password` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSy...` |

### Optional Variables
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DB_CONNECTION_NAME` | Cloud SQL connection name | `odiya-news-application:asia-south1:odiyanewsapp-fdc` | `project:region:instance` |
| `DB_USERNAME` | Database username | `postgres` | `myuser` |
| `DB_DATABASE` | Database name | `odiya-news-application-database` | `mydb` |
| `NEWS_BASE_URL` | News website URL | `https://odishatv.in` | `https://example.com` |
| `NEWS_SCRAPING_INTERVAL` | Cron schedule | `0 */3 * * *` | `0 */6 * * *` |
| `MAX_INSTANCES` | Firebase Functions max instances | `10` | `20` |
| `DEFAULT_ARTICLE_LIMIT` | Default articles per page | `10` | `20` |

### Database Pool Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `DB_POOL_SIZE` | Connection pool size | `5` |
| `DB_MAX_OVERFLOW` | Max overflow connections | `2` |
| `DB_POOL_TIMEOUT` | Pool timeout (seconds) | `30` |
| `DB_POOL_RECYCLE` | Connection recycle time (seconds) | `1800` |

## 🔒 Security Best Practices

### ✅ Do's
- Use environment variables in production
- Keep `config_local.py` in `.gitignore`
- Use strong, unique passwords
- Rotate API keys regularly
- Use Firebase environment configuration for production

### ❌ Don'ts
- Never commit `config_local.py` to version control
- Don't hardcode secrets in source code
- Don't share configuration files with sensitive data
- Don't use weak passwords or default credentials

## 🚀 Deployment

### Local Development
1. Create `config_local.py` with your values
2. Run the application locally

### Firebase Functions Deployment
1. Set environment variables in Firebase:
```bash
firebase functions:config:set db.password="your_password"
firebase functions:config:set gemini.api_key="your_api_key"
```

2. Deploy:
```bash
firebase deploy --only functions
```

### Environment Variables in Firebase
```bash
# Set database configuration
firebase functions:config:set \
  db.connection_name="your_connection_name" \
  db.username="postgres" \
  db.database="your_database" \
  db.password="your_password"

# Set API keys
firebase functions:config:set gemini.api_key="your_gemini_key"

# Set application settings
firebase functions:config:set \
  app.max_instances="10" \
  app.default_limit="10" \
  news.base_url="https://odishatv.in" \
  news.scraping_interval="0 */3 * * *"
```

## 🔍 Validation

The configuration system includes validation to ensure all required values are present:

```python
# This will raise an error if required config is missing
from config import config
if not config.validate_required_config():
    print("Configuration validation failed!")
```

## 📝 Troubleshooting

### Common Issues

1. **"Missing required configuration"**
   - Ensure `DB_PASSWORD` and `GEMINI_API_KEY` are set
   - Check that `config_local.py` exists and has correct values

2. **Database connection failed**
   - Verify database credentials
   - Check Cloud SQL instance is running
   - Ensure connection name is correct

3. **API key not working**
   - Verify Gemini API key is valid
   - Check API key has proper permissions
   - Ensure no extra spaces in the key

### Debug Mode
Enable debug logging to see configuration values (be careful in production):

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 Migration from Hardcoded Values

If you're migrating from the old hardcoded configuration:

1. **Database**: The old hardcoded password is now in `config.py` as a fallback
2. **API Keys**: The old hardcoded Gemini key is now in `config.py` as a fallback
3. **URLs**: All URLs are now configurable via environment variables

## 📞 Support

If you encounter issues with configuration:
1. Check this guide first
2. Verify all required variables are set
3. Check Firebase Functions logs for detailed error messages
4. Ensure your environment variables are properly formatted
