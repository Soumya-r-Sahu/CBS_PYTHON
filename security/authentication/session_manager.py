"""
Secure Session Management for Core Banking System

This module provides secure session management for web interfaces,
including session creation, validation, expiration, and anti-CSRF protection.
"""

import time
import logging
import secrets
import json
import hashlib
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta

# Import Flask-related modules if available
try:
    from flask import Flask, session, request, g, redirect, url_for
    from werkzeug.local import LocalProxy
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

# Import configuration
from security.config import SESSION_CONFIG
from security.logs.audit_logger import AuditLogger

# Configure logger
logger = logging.getLogger(__name__)


class SessionManager:
    """Manager for secure web session handling"""
    
    def __init__(self):
        """Initialize session manager with default configuration"""
        self.timeout_minutes = SESSION_CONFIG.get("session_timeout_minutes", 30)
        self.lifetime_hours = SESSION_CONFIG.get("session_lifetime_hours", 24)
        self.secure_cookie = SESSION_CONFIG.get("cookie_secure", True)
        self.httponly_cookie = SESSION_CONFIG.get("cookie_httponly", True)
        self.samesite = SESSION_CONFIG.get("cookie_samesite", "Strict")
        self.regenerate_on_login = SESSION_CONFIG.get("regenerate_id_on_login", True)
        
        # Initialize audit logger
        self.audit_logger = AuditLogger()
        
        # Store of active sessions (for memory-based mode)
        # In production, this would be replaced with Redis or similar
        self.active_sessions = {}
    
    def init_app(self, app: Any):
        """
        Initialize the session manager with a Flask application
        
        Args:
            app: Flask application instance
        """
        if not FLASK_AVAILABLE:
            logger.error("Flask is not available. Session management disabled.")
            return
        
        # Configure Flask session
        app.config["SESSION_COOKIE_SECURE"] = self.secure_cookie
        app.config["SESSION_COOKIE_HTTPONLY"] = self.httponly_cookie
        app.config["SESSION_COOKIE_SAMESITE"] = self.samesite
        app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=self.lifetime_hours)
        
        # Set a strong secret key if not already set
        if not app.secret_key:
            app.secret_key = secrets.token_hex(32)
            logger.warning("No Flask secret key found. Generated a random one - this will change on restart.")
        
        # Register before request handler for session management
        @app.before_request
        def check_session():
            # Skip for static files
            if request.path.startswith("/static/"):
                return None
            
            # Skip for public endpoints
            if self._is_public_endpoint(request.path):
                return None
            
            # Check if session exists
            if not session.get("user_id"):
                return redirect(url_for("login", next=request.path))
            
            # Check session expiry
            last_activity = session.get("last_activity", 0)
            if time.time() - last_activity > self.timeout_minutes * 60:
                # Session expired
                self.end_session()
                logger.info(f"Session expired for user {session.get('user_id')}")
                return redirect(url_for("login", next=request.path, reason="expired"))
            
            # Update last activity
            session["last_activity"] = time.time()
              # Validate session token authenticity
            session_id = session.get('session_id')
            user_id = session.get('user_id')
            
            # Verify the session token exists in our store
            if not self._validate_session_token(session_id, user_id):
                self.end_session()
                logger.warning(f"Invalid session token detected for user {user_id}")
                self.audit_logger.log_event(
                    event_type="security_violation",
                    user_id=user_id or "unknown",
                    description="Invalid session token",
                    metadata={
                        "path": request.path,
                        "method": request.method,
                        "remote_addr": request.remote_addr
                    }
                )
                return redirect(url_for("login", next=request.path, reason="invalid"))
            
            # Check CSRF token for mutating methods
            if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
                csrf_token = session.get("csrf_token")
                request_token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token") or request.json.get("csrf_token") if request.is_json else None
                
                # Validate CSRF token existence and match
                if not csrf_token or not request_token:
                    logger.warning(f"Missing CSRF token for {request.path}")
                    self.audit_logger.log_event(
                        event_type="security_violation",
                        user_id=user_id or "unknown",
                        description="Missing CSRF token",
                        metadata={
                            "path": request.path,
                            "method": request.method,
                            "remote_addr": request.remote_addr
                        }
                    )
                    return {"error": "CSRF token required", "code": "CSRF_REQUIRED"}, 403
                
                # Use secure constant time comparison to prevent timing attacks
                if not self._constant_time_compare(csrf_token, request_token):
                    logger.warning(f"CSRF token validation failed for {request.path}")
                    self.audit_logger.log_event(
                        event_type="security_violation",
                        user_id=session.get("user_id", "unknown"),
                        description="CSRF token validation failed",
                        metadata={
                            "path": request.path,
                            "method": request.method,
                            "remote_addr": request.remote_addr,
                            "user_agent": request.user_agent.string
                        }
                    )
                    return {"error": "Invalid CSRF token", "code": "INVALID_CSRF"}, 403
              # Validate IP address hasn't changed drastically (prevents session hijacking)
            if self._ip_has_changed_significantly(request.remote_addr, session.get('ip_address')):
                logger.warning(f"Suspicious IP change for user {user_id}: {session.get('ip_address')} -> {request.remote_addr}")
                self.audit_logger.log_event(
                    event_type="security_warning",
                    user_id=user_id or "unknown",
                    description="Suspicious IP address change",
                    metadata={
                        "original_ip": session.get('ip_address'),
                        "new_ip": request.remote_addr,
                        "path": request.path
                    }
                )
                # Update IP but add a flag to force re-authentication for sensitive operations
                session['ip_changed'] = True
                session['ip_address'] = request.remote_addr
                
            # Store user info in g for easy access
            g.user = self._get_user_info_from_session()
    
    def _validate_session_token(self, session_id: str, user_id: str) -> bool:
        """
        Validate that a session token exists and belongs to the specified user
        
        Args:
            session_id: Session ID to validate
            user_id: User ID that should own the session
            
        Returns:
            bool: True if session is valid, False otherwise
        """
        if not session_id or not user_id:
            return False
            
        # Check if session exists in our active sessions store
        stored_session = self.active_sessions.get(session_id)
        if not stored_session:
            return False
            
        # Check if session belongs to the right user
        if stored_session.get('user_id') != user_id:
            return False
            
        return True
    
    def _constant_time_compare(self, val1: str, val2: str) -> bool:
        """
        Compare two strings in constant time to prevent timing attacks
        
        Args:
            val1: First string to compare
            val2: Second string to compare
            
        Returns:
            bool: True if strings are equal, False otherwise
        """
        if val1 is None or val2 is None:
            return False
            
        if len(val1) != len(val2):
            return False
            
        result = 0
        for x, y in zip(val1, val2):
            result |= ord(x) ^ ord(y)
        return result == 0
        
    def _ip_has_changed_significantly(self, new_ip: str, old_ip: str) -> bool:
        """
        Check if IP address has changed significantly, beyond expected provider changes
        
        Args:
            new_ip: New IP address
            old_ip: Old IP address from session
            
        Returns:
            bool: True if significant change detected, False otherwise
        """
        if not old_ip:
            return False
            
        # Compare IP address bytes for significant changes
        # This is a simplified implementation - real one would use proper IP subnet analysis
        try:
            old_parts = [int(part) for part in old_ip.split('.')]
            new_parts = [int(part) for part in new_ip.split('.')]
            
            # Check first two octets (network portion often stays the same within an ISP)
            if (old_parts[0] != new_parts[0]) or (old_parts[1] != new_parts[1]):
                return True
                
            return False
        except (ValueError, IndexError):
            # If we can't parse the IP, assume it has changed
            return True
    
    def create_session(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new session for a user
        
        Args:
            user_data: User data to store in session
            
        Returns:
            Dict: Session information
        """
        if not FLASK_AVAILABLE:
            # Non-Flask mode (for API or other uses)
            return self._create_memory_session(user_data)
        
        # Flask mode
        session.clear()
        
        # If configured, regenerate session ID to prevent session fixation
        if self.regenerate_on_login and hasattr(session, "regenerate"):
            session.regenerate()
        
        # Store essential user data
        session["user_id"] = user_data.get("id") or user_data.get("user_id")
        session["username"] = user_data.get("username")
        session["roles"] = user_data.get("roles", [])
        
        # Store session metadata
        session["created_at"] = time.time()
        session["last_activity"] = time.time()
        session["ip_address"] = request.remote_addr
        session["user_agent"] = request.user_agent.string
        
        # Generate CSRF token
        session["csrf_token"] = secrets.token_hex(32)
        
        # Calculate expiry
        expiry = time.time() + (self.lifetime_hours * 3600)
        session["expiry"] = expiry
        
        # Log session creation
        self.audit_logger.log_event(
            event_type="session_created",
            user_id=session["user_id"],
            description=f"New session created for {session['username']}",
            metadata={
                "ip_address": session["ip_address"],
                "user_agent": session["user_agent"]
            }
        )
        
        return {
            "user_id": session["user_id"],
            "username": session["username"],
            "csrf_token": session["csrf_token"],
            "expiry": expiry
        }
    
    def _create_memory_session(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a memory-based session (non-Flask mode)
        
        Args:
            user_data: User data to store in session
            
        Returns:
            Dict: Session information including token
        """
        # Generate session token
        session_token = secrets.token_hex(32)
        
        # Create session data
        user_id = user_data.get("id") or user_data.get("user_id")
        csrf_token = secrets.token_hex(32)
        created_at = time.time()
        expiry = created_at + (self.lifetime_hours * 3600)
        
        # Store session
        self.active_sessions[session_token] = {
            "user_id": user_id,
            "username": user_data.get("username"),
            "roles": user_data.get("roles", []),
            "created_at": created_at,
            "last_activity": created_at,
            "ip_address": request.remote_addr if FLASK_AVAILABLE and request else "unknown",
            "user_agent": request.user_agent.string if FLASK_AVAILABLE and request and request.user_agent else "unknown",
            "csrf_token": csrf_token,
            "expiry": expiry
        }
        
        # Log session creation
        self.audit_logger.log_event(
            event_type="session_created",
            user_id=user_id,
            description=f"New memory session created for {user_data.get('username')}",
            metadata={
                "ip_address": self.active_sessions[session_token]["ip_address"],
                "user_agent": self.active_sessions[session_token]["user_agent"]
            }
        )
        
        return {
            "user_id": user_id,
            "username": user_data.get("username"),
            "session_token": session_token,
            "csrf_token": csrf_token,
            "expiry": expiry
        }
    
    def validate_session(self, session_token: Optional[str] = None) -> bool:
        """
        Validate a session
        
        Args:
            session_token: Session token (for non-Flask mode)
            
        Returns:
            bool: True if session is valid, False otherwise
        """
        if not FLASK_AVAILABLE or session_token:
            # Non-Flask mode
            if session_token not in self.active_sessions:
                return False
            
            session_data = self.active_sessions[session_token]
            
            # Check expiry
            if time.time() > session_data["expiry"]:
                # Session expired
                del self.active_sessions[session_token]
                return False
            
            # Check inactivity timeout
            if time.time() - session_data["last_activity"] > self.timeout_minutes * 60:
                # Session timeout
                del self.active_sessions[session_token]
                return False
            
            # Update last activity
            session_data["last_activity"] = time.time()
            return True
        
        # Flask mode - validate through before_request handler
        return "user_id" in session
    
    def end_session(self, session_token: Optional[str] = None) -> bool:
        """
        End a session
        
        Args:
            session_token: Session token (for non-Flask mode)
            
        Returns:
            bool: True if session was ended, False if not found
        """
        user_id = None
        
        if not FLASK_AVAILABLE or session_token:
            # Non-Flask mode
            if session_token in self.active_sessions:
                user_id = self.active_sessions[session_token].get("user_id")
                del self.active_sessions[session_token]
                
                # Log session end
                if user_id:
                    self.audit_logger.log_event(
                        event_type="session_ended",
                        user_id=user_id,
                        description=f"Session ended for user {user_id}",
                        metadata={"method": "token"}
                    )
                
                return True
            return False
        
        # Flask mode
        if "user_id" in session:
            user_id = session.get("user_id")
            session.clear()
            
            # Log session end
            if user_id:
                self.audit_logger.log_event(
                    event_type="session_ended",
                    user_id=user_id,
                    description=f"Session ended for user {user_id}",
                    metadata={"method": "flask"}
                )
            
            return True
        return False
    
    def get_csrf_token(self, session_token: Optional[str] = None) -> Optional[str]:
        """
        Get CSRF token for current session
        
        Args:
            session_token: Session token (for non-Flask mode)
            
        Returns:
            str: CSRF token or None if session not found
        """
        if not FLASK_AVAILABLE or session_token:
            # Non-Flask mode
            if session_token in self.active_sessions:
                return self.active_sessions[session_token].get("csrf_token")
            return None
        
        # Flask mode
        return session.get("csrf_token")
    
    def refresh_csrf_token(self, session_token: Optional[str] = None) -> Optional[str]:
        """
        Generate a new CSRF token for the session
        
        Args:
            session_token: Session token (for non-Flask mode)
            
        Returns:
            str: New CSRF token or None if session not found
        """
        new_token = secrets.token_hex(32)
        
        if not FLASK_AVAILABLE or session_token:
            # Non-Flask mode
            if session_token in self.active_sessions:
                self.active_sessions[session_token]["csrf_token"] = new_token
                return new_token
            return None
        
        # Flask mode
        if "user_id" in session:
            session["csrf_token"] = new_token
            return new_token
        return None
    
    def _is_public_endpoint(self, path: str) -> bool:
        """
        Check if an endpoint is public (not requiring authentication)
        
        Args:
            path: Request path
            
        Returns:
            bool: True if endpoint is public
        """
        public_paths = [
            "/login", "/logout", "/register", "/reset-password",
            "/static/", "/public/", "/health", "/api/public/"
        ]
        
        return any(path.startswith(p) for p in public_paths)
    
    def _get_user_info_from_session(self) -> Dict[str, Any]:
        """
        Get user info from session
        
        Returns:
            Dict: User information
        """
        return {
            "id": session.get("user_id"),
            "username": session.get("username"),
            "roles": session.get("roles", [])
        }
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from memory store
        
        Returns:
            int: Number of sessions cleaned up
        """
        # Only relevant for memory-based sessions
        if FLASK_AVAILABLE:
            return 0
        
        now = time.time()
        expired_tokens = []
        
        for token, session_data in self.active_sessions.items():
            # Check absolute expiry
            if now > session_data["expiry"]:
                expired_tokens.append(token)
                continue
            
            # Check inactivity timeout
            if now - session_data["last_activity"] > self.timeout_minutes * 60:
                expired_tokens.append(token)
        
        # Remove expired sessions
        for token in expired_tokens:
            del self.active_sessions[token]
        
        return len(expired_tokens)


# Create singleton instance
session_manager = SessionManager()

# Export main functions for easy access
create_session = session_manager.create_session
validate_session = session_manager.validate_session
end_session = session_manager.end_session
get_csrf_token = session_manager.get_csrf_token

# Create Flask template context processor
def csrf_token_context_processor():
    """Add CSRF token to template context"""
    if not FLASK_AVAILABLE:
        return {}
    
    return {
        "csrf_token": session.get("csrf_token", "")
    }


# Flask CSRF protection decorator
def csrf_protect(f):
    """
    Decorator to protect against CSRF attacks
    
    Args:
        f: Function to decorate
        
    Returns:
        Wrapped function with CSRF protection
    """
    if not FLASK_AVAILABLE:
        # If Flask is not available, just return the original function
        return f
    
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            csrf_token = session.get("csrf_token")
            request_token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
            
            if not csrf_token or not request_token or csrf_token != request_token:
                logger.warning(f"CSRF token validation failed for {request.path}")
                return {"error": "Invalid or missing CSRF token"}, 403
        
        return f(*args, **kwargs)
    
    return decorated_function
