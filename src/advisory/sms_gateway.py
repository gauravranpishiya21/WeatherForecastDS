"""SMS gateway integration for farmer alert delivery.

Config-driven generic HTTP SMS provider (MSG91 / Fast2SMS / government
NIC SMS gateway style): POST JSON {to, message} with bearer/API-key auth.
Defaults to dry-run (logs instead of sending) so the prototype is safe
to demo. Set sms_dry_run=false + provider credentials in .env to go live.
"""

from typing import Optional
import httpx
try:
    from loguru import logger
except ImportError:
    from src.utils.logger import logger


class SMSGateway:
    """Sends SMS alerts via a configurable HTTP gateway."""

    def __init__(
        self,
        provider: str = "console",
        api_key: str = "",
        sender_id: str = "SIHAGR",
        endpoint: str = "",
        dry_run: bool = True,
        timeout: float = 15.0,
    ):
        self.provider = provider
        self.api_key = api_key
        self.sender_id = sender_id
        self.endpoint = endpoint.rstrip("/")
        self.dry_run = dry_run
        self.timeout = timeout

    def _payload(self, phone: str, message: str) -> dict:
        if self.provider == "msg91":
            return {"flow_id": "", "sender": self.sender_id,
                    "mobiles": phone, "message": message}
        # generic default: Fast2SMS / NIC-style flat JSON
        return {"sender_id": self.sender_id, "message": message,
                "language": "english", "route": "q",
                "numbers": phone}

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["authorization"] = self.api_key
        return headers

    def send(self, phone: str, message: str) -> dict:
        """Send one SMS. Always safe: dry-run returns a simulated result."""
        phone = "".join(c for c in phone if c.isdigit())[-10:]
        if len(phone) != 10:
            return {"ok": False, "error": "invalid_phone"}
        if len(message) > 1000:
            message = message[:1000]
        if self.dry_run or not self.endpoint:
            logger.info(f"[SMS dry-run] to +91{phone}: {message[:80]}...")
            return {"ok": True, "dry_run": True, "to": f"+91{phone}",
                    "chars": len(message)}

        url = f"{self.endpoint}/sms/send"
        try:
            resp = httpx.post(url, json=self._payload(phone, message),
                              headers=self._headers(), timeout=self.timeout)
            resp.raise_for_status()
            logger.info(f"[SMS] sent to +91{phone} via {self.provider}")
            return {"ok": True, "dry_run": False, "to": f"+91{phone}",
                    "provider_response": resp.text[:200]}
        except Exception as e:
            logger.error(f"[SMS] send failed: {e}")
            return {"ok": False, "error": str(e)[:200]}
