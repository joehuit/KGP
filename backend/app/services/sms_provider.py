"""SMS gateway provider interface and verification service.

Defines the contract for real SMS dispatching (Twilio, local Algerian telecom aggregators),
alongside a local development provider strictly bounded to non-production environments.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import threading
from typing import Any, Dict, Optional, Tuple
from app.core.config import settings
from app.core.errors import AppException, AuthenticationError, ValidationError
from app.core.logging import logger


class BaseSMSProvider(ABC):
    """Abstract SMS Gateway contract."""

    @abstractmethod
    def send_verification_code(self, phone_number: str, code: str) -> bool:
        """Dispatch a one-time verification passcode to the recipient's phone number.
        Returns True if the provider accepted the message for delivery.
        """
        pass


class DevelopmentSMSProvider(BaseSMSProvider):
    """Local development & test SMS provider.
    Never sends actual SMS messages over telecom networks.
    Stores dispatched codes in memory and logs them for local developer visibility.
    STRICTLY FORBIDDEN IN PRODUCTION.
    """

    def __init__(self):
        self._sent_codes: Dict[str, str] = {}  # normalized phone -> latest code
        self._lock = threading.Lock()

    def send_verification_code(self, phone_number: str, code: str) -> bool:
        if settings.ENVIRONMENT in ("production", "staging"):
            logger.critical(
                "SECURITY HAZARD: DevelopmentSMSProvider invoked in %s environment! Refusing to execute.",
                settings.ENVIRONMENT,
            )
            return False

        with self._lock:
            self._sent_codes[phone_number] = code

        logger.info(
            "[DEV SMS DISPATCH] To: %s | Message: Your KGP LIST verification code is: %s (Expires in 5 min)",
            phone_number,
            code,
        )
        return True

    def get_last_code(self, phone_number: str) -> Optional[str]:
        """Test helper to retrieve the generated OTP without inspecting logs."""
        with self._lock:
            return self._sent_codes.get(phone_number)


class TwilioSMSProvider(BaseSMSProvider):
    """Production SMS provider integrating Twilio Programmable SMS API."""

    def __init__(self, account_sid: Optional[str] = None, auth_token: Optional[str] = None, from_number: Optional[str] = None):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    def send_verification_code(self, phone_number: str, code: str) -> bool:
        if not self.auth_token:
            logger.error("Twilio credentials not configured.")
            return False
        # Do not claim real delivery until live carrier API contract is activated
        logger.warning("Twilio carrier adapter invoked, but live carrier integration is pending activation.")
        raise AppException(
            message="Twilio SMS gateway integration is pending live carrier account activation.",
            code="SMS_GATEWAY_NOT_ACTIVATED",
            status_code=503,
        )


class AlgeriaTelecomSMSProvider(BaseSMSProvider):
    """Production SMS provider integrating Algerian local SMS aggregators (e.g. Mobilis / Ooredoo / Djezzy B2B).
    Requires active corporate aggregator contract and API key.
    """

    def __init__(self, api_key: Optional[str] = None, sender_id: str = "KGPLIST"):
        self.api_key = api_key
        self.sender_id = sender_id

    def send_verification_code(self, phone_number: str, code: str) -> bool:
        if not self.api_key:
            logger.error("Algerian SMS Aggregator API key not configured.")
            return False
        # Do not claim real delivery until live carrier API contract is activated
        logger.warning("Algerian Telecom carrier adapter invoked, but corporate aggregator contract is pending activation.")
        raise AppException(
            message="Algerian telecom aggregator integration is pending corporate contract activation.",
            code="SMS_GATEWAY_NOT_ACTIVATED",
            status_code=503,
        )


# Factory to resolve active SMS Provider
def get_sms_provider() -> BaseSMSProvider:
    """Return the configured SMS provider instance based on environment settings."""
    if settings.ENVIRONMENT in ("production", "staging"):
        if settings.SMS_GATEWAY_PROVIDER == "twilio":
            if not settings.SMS_API_KEY:
                raise AppException(
                    message="Twilio SMS API key required in production/staging.",
                    code="SMS_CREDENTIALS_MISSING",
                    status_code=503,
                )
            return TwilioSMSProvider(auth_token=settings.SMS_API_KEY)
        elif settings.SMS_GATEWAY_PROVIDER == "algeria_telecom":
            if not settings.SMS_API_KEY:
                raise AppException(
                    message="Algerian Telecom SMS API key required in production/staging.",
                    code="SMS_CREDENTIALS_MISSING",
                    status_code=503,
                )
            return AlgeriaTelecomSMSProvider(api_key=settings.SMS_API_KEY)
        else:
            raise AppException(
                message="No production SMS gateway configured. Set SMS_GATEWAY_PROVIDER and SMS_API_KEY in production/staging.",
                code="SMS_GATEWAY_NOT_CONFIGURED",
                status_code=503,
            )
    return _dev_sms_provider


_dev_sms_provider = DevelopmentSMSProvider()


class OTPVerificationService:
    """Manages generation, secure hashing, dispatch, and verification of one-time passcodes.
    Features:
    - Salted SHA-256 code hashing (plaintext codes never kept in memory or DB)
    - 5-minute strict expiration
    - Maximum 3 incorrect attempts per challenge to prevent brute-force attacks
    """

    def __init__(self, provider: Optional[BaseSMSProvider] = None):
        self._provider = provider or _dev_sms_provider
        self._challenges: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def generate_and_send_otp(self, phone_number: str) -> bool:
        """Create a cryptographically secure 6-digit OTP and dispatch via SMS provider."""
        # Generate 6-digit numeric code: 100000 - 999999
        code = f"{secrets.randbelow(900000) + 100000}"
        salt = secrets.token_hex(16)
        hashed_code = hashlib.sha256((salt + code).encode("utf-8")).hexdigest()

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=5)

        with self._lock:
            self._challenges[phone_number] = {
                "hash": hashed_code,
                "salt": salt,
                "expires_at": expires_at,
                "attempts": 0,
            }

        # Dispatch via SMS provider
        provider = get_sms_provider()
        return provider.send_verification_code(phone_number, code)

    def verify_otp(self, phone_number: str, code: str) -> bool:
        """Verify the submitted code against the active challenge for the phone number."""
        now = datetime.now(timezone.utc)

        with self._lock:
            challenge = self._challenges.get(phone_number)
            if not challenge:
                raise AuthenticationError("No pending verification request for this phone number. Please request a new code.")

            if now > challenge["expires_at"]:
                del self._challenges[phone_number]
                raise AuthenticationError("Verification code has expired. Please request a new code.")

            challenge["attempts"] += 1
            if challenge["attempts"] > 3:
                del self._challenges[phone_number]
                raise AuthenticationError("Too many incorrect attempts. Please request a new verification code.")

            # Constant-time comparison of hashed code
            expected_hash = hashlib.sha256((challenge["salt"] + code.strip()).encode("utf-8")).hexdigest()
            if not secrets.compare_digest(challenge["hash"], expected_hash):
                remaining = 3 - challenge["attempts"]
                raise AuthenticationError(f"Incorrect verification code. {remaining} attempt(s) remaining.")

            # Successful verification - consume challenge immediately
            del self._challenges[phone_number]
            return True


# Global OTP verification service instance
otp_verification_service = OTPVerificationService()
