"""
Content Security Policy (CSP) Manager for Core Banking System

This module provides functionality to generate and manage Content Security
Policy headers to prevent Cross-Site Scripting (XSS) and other client-side attacks.
"""

import logging
from typing import Dict, List, Optional, Union, Set
from flask import Flask, Response

# Configure logger
logger = logging.getLogger(__name__)


class CSPManager:
    """Manager for Content Security Policy configuration and implementation"""
    
    def __init__(self):
        """Initialize CSP Manager with default policy"""
        # Initialize default CSP directives
        self.directives = {
            # Restricts from where the protected resource can load content
            "default-src": ["'self'"],
            
            # Restricts from where the protected resource can load scripts
            "script-src": ["'self'"],
            
            # Restricts from where the protected resource can load CSS
            "style-src": ["'self'"],
            
            # Restricts from where the protected resource can load images
            "img-src": ["'self'", "data:"],
            
            # Restricts from where the protected resource can load fonts
            "font-src": ["'self'"],
            
            # Restricts from where the protected resource can load objects (<object>, <embed>, <applet>)
            "object-src": ["'none'"],
            
            # Restricts from where the protected resource can load frames
            "frame-src": ["'self'"],
            
            # Restricts from where the protected resource can connect (XMLHttpRequest, WebSockets, etc.)
            "connect-src": ["'self'"],
            
            # Restricts from where the protected resource can be framed
            "frame-ancestors": ["'self'"],
            
            # Restricts where forms can be submitted to
            "form-action": ["'self'"],
            
            # Restricts what can be used as the <base> tag
            "base-uri": ["'self'"],
            
            # Enables reporting of CSP violations
            "report-uri": ["/api/security/csp-report"]
        }
        
        # Initialize report-only mode (doesn't block, only reports violations)
        self.report_only = False
        
        # Flag to enable or disable CSP
        self.enabled = True
        
        # Store nonces for script-src and style-src
        self.nonces = set()
    
    def add_directive(self, directive: str, value: Union[str, List[str]]) -> None:
        """
        Add or update a CSP directive
        
        Args:
            directive (str): CSP directive name
            value (Union[str, List[str]]): Value(s) for the directive
        """
        if directive not in self.directives:
            self.directives[directive] = []
        
        if isinstance(value, str):
            if value not in self.directives[directive]:
                self.directives[directive].append(value)
        else:
            for val in value:
                if val not in self.directives[directive]:
                    self.directives[directive].append(val)
    
    def remove_directive(self, directive: str) -> None:
        """
        Remove a CSP directive
        
        Args:
            directive (str): CSP directive name to remove
        """
        if directive in self.directives:
            del self.directives[directive]
    
    def clear_directive(self, directive: str) -> None:
        """
        Clear all values for a CSP directive
        
        Args:
            directive (str): CSP directive name to clear
        """
        if directive in self.directives:
            self.directives[directive] = []
    
    def set_report_only(self, report_only: bool) -> None:
        """
        Set report-only mode
        
        Args:
            report_only (bool): Whether to use report-only mode
        """
        self.report_only = report_only
    
    def enable(self) -> None:
        """Enable Content Security Policy"""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable Content Security Policy"""
        self.enabled = False
    
    def generate_csp_header(self) -> Dict[str, str]:
        """
        Generate CSP header
        
        Returns:
            Dict[str, str]: CSP header name and value
        """
        if not self.enabled:
            return {}
        
        # Build CSP header value
        csp_value = ""
        
        for directive, values in self.directives.items():
            if not values:
                continue
            
            csp_value += directive
            for value in values:
                csp_value += f" {value}"
            csp_value += "; "
        
        # Remove trailing semicolon and space
        if csp_value.endswith("; "):
            csp_value = csp_value[:-2]
        
        # Determine header name based on mode
        header_name = (
            "Content-Security-Policy-Report-Only"
            if self.report_only
            else "Content-Security-Policy"
        )
        
        return {header_name: csp_value}
    
    def apply_csp_header(self, response: Response) -> Response:
        """
        Apply CSP header to a Flask response
        
        Args:
            response (Response): Flask response object
            
        Returns:
            Response: Modified response with CSP headers
        """
        if not self.enabled:
            return response
        
        # Generate CSP header
        csp_header = self.generate_csp_header()
        
        # Apply header to response
        for header_name, header_value in csp_header.items():
            response.headers[header_name] = header_value
        
        return response
    
    def generate_nonce(self) -> str:
        """
        Generate a nonce for use in script-src and style-src directives
        
        Returns:
            str: Generated nonce
        """
        import secrets
        
        # Generate a secure random nonce
        nonce = secrets.token_urlsafe(16)
        
        # Add nonce to script-src and style-src directives
        for directive in ["script-src", "style-src"]:
            nonce_value = f"'nonce-{nonce}'"
            self.add_directive(directive, nonce_value)
        
        # Store nonce
        self.nonces.add(nonce)
        
        return nonce
    
    def clear_nonces(self) -> None:
        """Clear all stored nonces and remove from directives"""
        for directive in ["script-src", "style-src"]:
            if directive in self.directives:
                # Keep only values that are not nonces
                self.directives[directive] = [
                    value for value in self.directives[directive]
                    if not value.startswith("'nonce-")
                ]
        
        # Clear nonce set
        self.nonces.clear()
    
    def create_flask_middleware(self, app: Flask) -> None:
        """
        Create Flask middleware to apply CSP headers
        
        Args:
            app (Flask): Flask application instance
        """
        # Register after-request handler
        @app.after_request
        def add_csp_header(response):
            return self.apply_csp_header(response)
    
    def create_csp_report_endpoint(self, app: Flask) -> None:
        """
        Create endpoint for CSP violation reports
        
        Args:
            app (Flask): Flask application instance
        """
        from flask import request, jsonify
        
        @app.route("/api/security/csp-report", methods=["POST"])
        def csp_report():
            # Log CSP violation report
            report = request.get_json()
            logger.warning(f"CSP Violation: {report}")
            
            return jsonify({"status": "report-received"}), 204


# Create singleton instance
csp_manager = CSPManager()

# Export functions for easy access
add_directive = csp_manager.add_directive
remove_directive = csp_manager.remove_directive
clear_directive = csp_manager.clear_directive
set_report_only = csp_manager.set_report_only
enable_csp = csp_manager.enable
disable_csp = csp_manager.disable
generate_nonce = csp_manager.generate_nonce
clear_nonces = csp_manager.clear_nonces
