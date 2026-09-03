"""LLM-powered agro-advisory generator (Google Gen AI SDK).

Uses the current `google-genai` package
(`from google import genai`, NOT the deprecated `google-generativeai`)
with a configurable, currently-supported model name
(default `gemini-3.5-flash`, override via GEMINI_MODEL / constructor).

Single client instance per generator. Template fallback when no API
key is configured or the SDK is not installed — the pipeline never breaks.
"""

from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from .crop_rules import CropAdvisory
from .risk_assessment import WeatherRisk
from ..utils.translation import get_translation, get_risk_label, translate_text_simple

DEFAULT_MODEL = "gemini-3.5-flash"

try:
    from google import genai as google_genai
    from google.genai import types as google_types
    GENAI_AVAILABLE = True
except ImportError:
    google_genai = None
    google_types = None
    GENAI_AVAILABLE = False
    logger.warning("google-genai not installed. Using template-based fallback.")

# Hard timeout so a hung LLM call fails fast into template fallback
# instead of stalling the API request for minutes.
LLM_TIMEOUT_MS = 45000


class AdvisoryResponse(BaseModel):
    """Structured advisory response with multi-language support."""
    advisory_text: str
    language: str
    sms_version: str
    template_version: str = ""
    model_used: str = "template"


class LLMAdvisoryGenerator:
    """Generates natural language agro-advisories using the Gemini API."""

    def __init__(self, api_key: Optional[str] = None,
                 model_name: Optional[str] = None):
        self.model_name = model_name or DEFAULT_MODEL
        self.client = None
        if api_key and GENAI_AVAILABLE:
            try:
                self.client = google_genai.Client(
                    api_key=api_key,
                    http_options=google_types.HttpOptions(timeout=LLM_TIMEOUT_MS),
                )
                logger.info(f"Gemini client ready (model={self.model_name})")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")
                self.client = None
        elif not api_key:
            logger.info("No Gemini API key provided. Using template-based advisory generation.")

    def _generate(self, prompt: str) -> Optional[str]:
        """One LLM call. Returns stripped text, or None on any failure."""
        if self.client is None:
            return None
        try:
            resp = self.client.models.generate_content(
                model=self.model_name, contents=prompt
            )
            text = (resp.text or "").strip()
            return text or None
        except Exception as e:
            logger.error(f"Gemini call failed (model={self.model_name}): {e}")
            return None

    def generate_advisory(
        self,
        crop_advisory: CropAdvisory,
        weather_risks: List[WeatherRisk],
        location_info: str,
        language: str = 'en',
    ) -> AdvisoryResponse:
        """Generate a detailed natural language advisory.

        Always builds the offline template version first; upgrades to the
        LLM version only if the single API call succeeds.
        """
        template_text = self._build_template_advisory(
            crop_advisory, weather_risks, location_info, language
        )

        llm_text = self._generate(self._build_llm_prompt(
            crop_advisory, weather_risks, location_info, language
        )) if self.client else None

        if llm_text:
            advisory_text = llm_text
            model_used = self.model_name
        else:
            advisory_text = template_text
            model_used = "template"

        sms_text = self._generate_sms_from_text(advisory_text)
        if language != 'en':
            sms_text = self._translate_sms(sms_text, language)

        return AdvisoryResponse(
            advisory_text=advisory_text,
            language=language,
            sms_version=sms_text,
            template_version=template_text,
            model_used=model_used,
        )

    def _build_llm_prompt(
        self,
        crop_advisory: CropAdvisory,
        weather_risks: List[WeatherRisk],
        location_info: str,
        language: str,
    ) -> str:
        """Build the prompt for the Gemini API."""
        lang_instruction = ""
        if language == 'hi':
            lang_instruction = "\nPlease respond entirely in Hindi (Devanagari script)."
        elif language == 'ta':
            lang_instruction = "\nPlease respond entirely in Tamil."
        elif language == 'te':
            lang_instruction = "\nPlease respond entirely in Telugu."
        elif language == 'mr':
            lang_instruction = "\nPlease respond entirely in Marathi."

        prompt = f"""You are an expert Indian agronomist providing advice to smallholder farmers.

Location: {location_info}
Crop: {crop_advisory.crop_name}
Current Growth Stage: {crop_advisory.growth_stage}
Overall Risk Level: {crop_advisory.risk_level}
{lang_instruction}

Rule-based action items:
"""
        for item in crop_advisory.action_items:
            prompt += f"- [{item.category}] {item.advice}\n"

        if weather_risks:
            prompt += "\nWeather Risks:\n"
            for risk in weather_risks:
                prompt += f"- {risk.risk_type} (Severity: {risk.severity}/100): {risk.description}\n"
                prompt += f"  Actions: {', '.join(risk.recommended_actions)}\n"

        prompt += """
Provide a clear, actionable advisory in simple language that a farmer can understand.
Structure the advisory with:
1. Current weather summary (2-3 sentences)
2. Key risks to watch (bullet points)
3. Today's recommended actions (numbered steps)
4. What to do in the next 3 days

Keep sentences short and practical. Avoid technical jargon.
"""
        return prompt

    def _build_template_advisory(
        self,
        crop_advisory: CropAdvisory,
        weather_risks: List[WeatherRisk],
        location_info: str,
        language: str,
    ) -> str:
        """Build a template-based advisory (works without LLM API)."""
        title = get_translation("advisory_title", language)
        risk_label = get_translation("risk_level", language)
        risk_value = get_risk_label(crop_advisory.risk_level, language)

        lines = [
            f"=== {title} ===",
            "",
            f"📍 {get_translation('location_label', language)}: {location_info}",
            f"🌾 {get_translation('crop_label', language)}: {crop_advisory.crop_name}",
            f"🌱 {get_translation('stage_label', language)}: {crop_advisory.growth_stage}",
            f"⚠️  {risk_label}: {risk_value}",
            "",
            f"--- {get_translation('advisory_label', language)} ---",
            "",
        ]

        for item in crop_advisory.action_items:
            lines.append(f"• [{item.category}] {item.advice}")

        if weather_risks:
            lines.append("")
            lines.append(f"--- {get_translation('risk_summary', language)} ---")
            for risk in weather_risks:
                sev_label = get_risk_label(
                    "CRITICAL" if risk.severity >= 80
                    else "HIGH" if risk.severity >= 60
                    else "MODERATE" if risk.severity >= 30 else "LOW",
                    language,
                )
                lines.append(f"• {risk.risk_type} ({sev_label}): {risk.description}")
                for action in risk.recommended_actions[:2]:
                    lines.append(f"  → {action}")

        return "\n".join(lines)

    def _generate_sms_from_text(self, advisory_text: str, max_chars: int = 160) -> str:
        """Generate a concise SMS version from advisory text."""
        if len(advisory_text) <= max_chars:
            return advisory_text

        llm_sms = None
        if self.client:
            llm_sms = self._generate(
                f"Summarize this agricultural advisory in under {max_chars} characters. "
                f"Keep only the most critical actions:\n\n{advisory_text}"
            )
        if llm_sms and len(llm_sms) <= max_chars:
            return llm_sms

        truncated = advisory_text[:max_chars - 3]
        last_period = truncated.rfind('.')
        if last_period > max_chars // 2:
            return truncated[:last_period + 1]
        return truncated + "..."

    def _translate_sms(self, text: str, target_language: str) -> str:
        """Translate SMS text using the LLM or keyword fallback."""
        if self.client:
            translated = self._generate(
                f"Translate this agricultural SMS advisory into {target_language}. "
                f"Keep it under 160 characters:\n\n{text}"
            )
            if translated and len(translated) <= 160:
                return translated
        return translate_text_simple(text, target_language)

    def generate_sms_advisory(self, advisory_text: str, max_chars: int = 160) -> str:
        """Public method to generate SMS version."""
        return self._generate_sms_from_text(advisory_text, max_chars)

    def translate_advisory(self, text: str, target_language: str) -> str:
        """Translate advisory text to a target language."""
        if self.client:
            translated = self._generate(
                "Translate the following agricultural advisory into "
                f"{target_language}. Maintain technical accuracy but keep it "
                f"farmer-friendly:\n\n{text}"
            )
            if translated:
                return translated
        return translate_text_simple(text, target_language)
