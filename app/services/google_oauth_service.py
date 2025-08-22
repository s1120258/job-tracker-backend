# app/services/google_oauth_service.py

import httpx
from typing import Optional, Dict, Any
from authlib.jose import jwt
from authlib.jose.errors import JoseError
from app.core.config import settings
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class GoogleOAuth2Service:
    """
    Google OAuth2 authentication service for frontend-driven auth flow.
    Handles ID token verification and user info extraction.
    """
    
    GOOGLE_TOKEN_VERIFY_URL = "https://oauth2.googleapis.com/tokeninfo"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        
        if not self.client_id:
            raise ValueError("GOOGLE_CLIENT_ID must be set in environment variables")
    
    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify Google ID token and extract user information.
        
        Args:
            id_token: JWT ID token from Google
            
        Returns:
            Dict containing user info (sub, email, name, given_name, family_name, picture)
            
        Raises:
            HTTPException: If token verification fails
        """
        try:
            # Fetch Google's public keys for JWT verification
            async with httpx.AsyncClient() as client:
                response = await client.get(self.GOOGLE_JWKS_URL)
                response.raise_for_status()
                jwks = response.json()
            
            # Verify and decode the ID token
            try:
                claims = jwt.decode(
                    id_token, 
                    jwks,
                    claims_options={
                        "aud": {"essential": True, "value": self.client_id},
                        "iss": {"essential": True, "values": [
                            "https://accounts.google.com",
                            "accounts.google.com"
                        ]},
                    }
                )
            except JoseError as e:
                logger.error(f"JWT verification failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid ID token"
                )
            
            # Extract required user information
            user_info = {
                "google_id": claims.get("sub"),
                "email": claims.get("email"),
                "given_name": claims.get("given_name", ""),
                "family_name": claims.get("family_name", ""),
                "name": claims.get("name", ""),
                "picture": claims.get("picture"),
                "email_verified": claims.get("email_verified", False),
            }
            
            # Validate required fields
            if not user_info["google_id"] or not user_info["email"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing required user information in ID token"
                )
            
            if not user_info["email_verified"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email not verified by Google"
                )
            
            logger.info(f"Successfully verified Google ID token for user: {user_info['email']}")
            return user_info
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch Google JWKS: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google authentication service unavailable"
            )
        except Exception as e:
            logger.error(f"Unexpected error during ID token verification: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Google using access token (alternative method).
        
        Args:
            access_token: Google access token
            
        Returns:
            Dict containing user info
            
        Raises:
            HTTPException: If request fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.GOOGLE_USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                user_info = response.json()
                
                logger.info(f"Successfully retrieved user info for: {user_info.get('email')}")
                return user_info
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to get user info from Google: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token"
            )
    
    def parse_user_data(self, google_user_info: Dict[str, Any]) -> Dict[str, str]:
        """
        Parse and normalize Google user data for database storage.
        
        Args:
            google_user_info: Raw user info from Google
            
        Returns:
            Dict with normalized user data
        """
        # Extract first and last names
        given_name = google_user_info.get("given_name", "")
        family_name = google_user_info.get("family_name", "")
        
        # Fallback to parsing full name if given/family names are not available
        if not given_name and not family_name:
            full_name = google_user_info.get("name", "")
            if full_name:
                name_parts = full_name.split()
                given_name = name_parts[0] if name_parts else "Unknown"
                family_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "User"
            else:
                given_name = "Unknown"
                family_name = "User"
        
        return {
            "google_id": google_user_info["google_id"],
            "email": google_user_info["email"],
            "firstname": given_name or "Unknown",
            "lastname": family_name or "User",
            "provider": "google",
            "is_oauth": True,
        }


# Create a singleton instance
google_oauth_service = GoogleOAuth2Service()
