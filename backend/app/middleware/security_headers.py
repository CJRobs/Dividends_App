"""
Security Headers Middleware

Adds HTTP security headers to all responses to protect against common web vulnerabilities.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000; includeSubDomains
    - Content-Security-Policy: default-src 'self'
    - X-Permitted-Cross-Domain-Policies: none
    - Referrer-Policy: strict-origin-when-cross-origin
    """

    async def dispatch(self, request: Request, call_next):
        """Process request and add security headers to response."""
        response: Response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Prevent clickjacking by disallowing iframe embedding
        response.headers['X-Frame-Options'] = 'DENY'

        # Enable XSS protection in browsers
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Enforce HTTPS for 1 year (including subdomains)
        # Note: Only enable this if you're using HTTPS!
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Content Security Policy - restrict resources to same origin
        # Adjust this if you need to load resources from other domains
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"

        # Restrict Flash and PDF cross-domain policies
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'

        # Control referrer information
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Remove server header to avoid revealing server software
        if 'Server' in response.headers:
            del response.headers['Server']

        return response
