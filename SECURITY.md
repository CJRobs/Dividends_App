# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please handle it responsibly:

1. **Do not** create a public GitHub issue
2. Email the repository owner directly with details
3. Include steps to reproduce the vulnerability
4. Allow reasonable time for a fix before public disclosure

## Security Best Practices

### API Keys

- **Never commit API keys to git** - API keys should never be stored in version control
- **Rotate keys regularly** - Change your Alpha Vantage API key periodically
- **Use environment variables** - All secrets must be stored in `.env` files
- **Keep `.env` in `.gitignore`** - Ensure environment files are never tracked

### Data Protection

- **CSV data files are excluded from git** - Your dividend data contains personal financial information
- **Ensure proper file permissions** - Restrict read access to data directory (`chmod 600` for sensitive files)
- **Regularly backup your data** - Keep backups of your dividend data in a secure location
- **Never share raw data** - Avoid sharing your dividend CSV files publicly

### Application Security

- **Run backend with least-privilege user** - Don't run the application as root
- **Use HTTPS in production** - Configure a reverse proxy (nginx/caddy) with TLS certificates
- **Keep dependencies updated** - Regularly update Python and Node.js packages
- **Review logs regularly** - Monitor `backend/logs/app.log` for suspicious activity
- **Validate all inputs** - The application validates data schema and file paths

## Security Features Implemented

### Environment Variable Validation

- API key format validation at startup
- Rejects placeholder/invalid API keys
- Data path validation
- Environment-specific configurations

### Structured Logging

- All application events logged with timestamps
- Request/response logging for audit trail
- Log rotation (10MB max size, 5 backup files)
- Separate log levels for development and production
- Sensitive data (API keys) never logged

### Input Validation

- File existence checks before data loading
- File permission validation
- Data schema validation against required columns
- Graceful degradation on data load failure
- Comprehensive error handling with specific error types

### Data Integrity

- DataFrame schema validation
- Required column checks (Time, Ticker, Name, Total)
- Empty data detection
- Corrupt CSV handling

## Configuration Security

### Environment Variables

The application requires the following environment variables (see `.env.example`):

```env
ALPHA_VANTAGE_API_KEY=your_api_key_here  # Required - Get from alphavantage.co
ENVIRONMENT=development                   # development or production
DATA_PATH=../data/dividends.csv          # Path to your dividend data
```

### Startup Validation

On startup, the application:
1. Validates API key is configured and not a placeholder
2. Checks data file exists and is readable
3. Validates data schema matches expected format
4. Starts in degraded mode if validation fails

### Logging Security

Logs are stored in `backend/logs/` (production only):
- Automatic rotation prevents disk space exhaustion
- Logs include request/response details for auditing
- No sensitive data (passwords, API keys) in logs
- Timestamped entries for forensic analysis

## Deployment Security

### Development Environment

```bash
# Use development mode for debugging
export ENVIRONMENT=development

# Logs go to console only
cd backend && uvicorn app.main:app --reload
```

### Production Environment

```bash
# Use production mode for deployment
export ENVIRONMENT=production

# Logs go to console + file with rotation
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Production Checklist:**
- [ ] Rotate API keys before deployment
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Configure reverse proxy with HTTPS
- [ ] Restrict file permissions on `.env` and data files
- [ ] Set up log monitoring/alerting
- [ ] Regular security updates for dependencies
- [ ] Firewall rules limiting access to backend port

## Known Security Considerations

### API Rate Limiting

The application implements client-side rate limiting for Alpha Vantage API:
- 0.2 second delay between requests
- Cached responses (24 hours for fundamental data)
- No server-side rate limiting on API endpoints

**Recommendation for Production:** Add rate limiting middleware (e.g., `slowapi`) to prevent abuse.

### CORS Configuration

CORS is configured for `localhost:3000` by default:
- Allows credentials
- Allows all methods and headers
- **For production:** Restrict to specific production domains

### Authentication

**Current State:** No authentication implemented

**Recommendation for Production:**
- Add user authentication (OAuth2, JWT)
- Implement role-based access control
- Add API key authentication for external access
- Session management for frontend

### Data Privacy

- Dividend data is personal financial information
- Application assumes single-user deployment
- No built-in multi-tenant support
- **For production:** Ensure proper user isolation if deploying for multiple users

## Security Updates

### Dependency Management

Keep dependencies updated:

```bash
# Backend
cd backend
pip list --outdated
pip install --upgrade -r requirements.txt

# Frontend
cd frontend
npm outdated
npm update
```

### Security Scanning

Recommended tools:
- `pip-audit` - Scan Python dependencies for known vulnerabilities
- `npm audit` - Scan Node.js dependencies for vulnerabilities
- `bandit` - Security linter for Python code
- `eslint-plugin-security` - Security linter for JavaScript

## Incident Response

If a security incident occurs:

1. **Immediate Actions:**
   - Rotate all API keys immediately
   - Review logs for unauthorized access
   - Backup current state for forensics
   - Disconnect from network if necessary

2. **Investigation:**
   - Check `backend/logs/app.log` for suspicious requests
   - Review git history for unauthorized changes
   - Examine data files for modifications

3. **Recovery:**
   - Restore from clean backup if compromised
   - Update all credentials
   - Patch vulnerability
   - Monitor for further issues

4. **Post-Incident:**
   - Document incident and response
   - Update security measures
   - Consider additional monitoring

## Contact

For security concerns, please contact the repository maintainer directly rather than opening public issues.
