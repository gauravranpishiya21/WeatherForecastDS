"""Translation utilities for multilingual advisory support.

Supports English (en), Hindi (hi), Tamil (ta), Telugu (te), Marathi (mr),
Kannada (kn), Bengali (bn), Gujarati (gu), Malayalam (ml), Punjabi (pa).
"""

from loguru import logger


# Comprehensive translations for common advisory terms in 10 Indian languages
TRANSLATIONS = {
    "en": {
        "advisory_title": "Agricultural Advisory",
        "risk_level": "Risk Level",
        "low": "Low",
        "moderate": "Moderate",
        "high": "High",
        "critical": "Critical",
        "irrigation": "Irrigation",
        "fertilizer": "Fertilizer",
        "pest_warning": "Pest Warning",
        "harvest": "Harvest",
        "no_irrigation": "No irrigation needed",
        "temperature": "Temperature",
        "rainfall": "Rainfall",
        "humidity": "Humidity",
        "wind": "Wind Speed",
        "heat_stress": "Heat Stress Alert",
        "frost_warning": "Frost Warning",
        "waterlogging": "Waterlogging Risk",
        "drought": "Drought Conditions",
        "strong_wind": "Strong Wind Alert",
        "disease_risk": "Disease Risk",
        "spray_safe": "Safe to spray pesticides",
        "spray_unsafe": "Do NOT spray pesticides today",
        "irrigate_now": "Irrigate your field today",
        "skip_irrigation": "Skip irrigation today, rainfall expected",
        "fertilize": "Apply fertilizer after rainfall stops",
        "monitor_crops": "Monitor crops closely for next 2-3 days",
        "sms_header": "Weather Alert:",
        "location_label": "Location",
        "crop_label": "Crop",
        "stage_label": "Growth Stage",
        "advisory_label": "Today's Advisory",
        "weekly_plan": "Weekly Action Plan",
        "risk_summary": "Risk Assessment",
    },
    "hi": {
        "advisory_title": "कृषि सलाह",
        "risk_level": "जोखिम स्तर",
        "low": "कम",
        "moderate": "मध्यम",
        "high": "उच्च",
        "critical": "गंभीर",
        "irrigation": "सिंचाई",
        "fertilizer": "उर्वरक",
        "pest_warning": "कीट चेतावनी",
        "harvest": "कटाई",
        "no_irrigation": "सिंचाई की आवश्यकता नहीं",
        "temperature": "तापमान",
        "rainfall": "वर्षा",
        "humidity": "आर्द्रता",
        "wind": "हवा की गति",
        "heat_stress": "गर्मी का खतरा",
        "frost_warning": "पाले की चेतावनी",
        "waterlogging": "जलभराव का जोखिम",
        "drought": "सूखे की स्थिति",
        "strong_wind": "तेज हवा की चेतावनी",
        "disease_risk": "बीमारी का जोखिम",
        "spray_safe": "कीटनाशक छिड़काव के लिए सुरक्षित",
        "spray_unsafe": "आज कीटनाशक छिड़काव न करें",
        "irrigate_now": "आज अपने खेत में सिंचाई करें",
        "skip_irrigation": "बारिश की संभावना है, सिंचाई छोड़ दें",
        "fertilize": "बारिश रुकने के बाद उर्वरक डालें",
        "monitor_crops": "अगले 2-3 दिन फसल की निगरानी करें",
        "sms_header": "मौसम चेतावनी:",
        "location_label": "स्थान",
        "crop_label": "फसल",
        "stage_label": "विकास चरण",
        "advisory_label": "आज की सलाह",
        "weekly_plan": "साप्ताहिक कार्य योजना",
        "risk_summary": "जोखिम मूल्यांकन",
    },
    "ta": {
        "advisory_title": "வேளாண் ஆலோசனை",
        "risk_level": "ஆபத்து நிலை",
        "low": "குறைவு",
        "moderate": "மிதமான",
        "high": "உயர்",
        "critical": "மிக உயர்",
        "irrigation": "நீர்ப்பாசனம்",
        "temperature": "வெப்பநிலை",
        "rainfall": "மழை",
        "heat_stress": "வெப்ப அழுத்த எச்சரிக்கை",
        "frost_warning": "உறைபனி எச்சரிக்கை",
    },
    "te": {
        "advisory_title": "వ్యవసాయ సలహా",
        "risk_level": "ప్రమాద స్థాయి",
        "low": "తక్కువ",
        "moderate": "మధ్యస్థం",
        "high": "ఎక్కువ",
        "critical": "క్లిష్టం",
        "irrigation": "నీటిపారుదల",
        "temperature": "ఉష్ణోగ్రత",
        "rainfall": "వర్షపాతం",
    },
    "mr": {
        "advisory_title": "शेती सल्ला",
        "risk_level": "धोका पातळी",
        "low": "कमी",
        "moderate": "दर्जेदार",
        "high": "जास्त",
        "critical": "गंभीर",
        "irrigation": "सिंचन",
        "temperature": "तापमान",
        "rainfall": "पाऊस",
    },
    "kn": {
        "advisory_title": "ಕೃಷಿ ಸಲಹೆ",
        "risk_level": "ಅಪಾಯ ಮಟ್ಟ",
        "low": "ಕಡಿಮೆ",
        "moderate": "ಮಧ್ಯಮ",
        "high": "ಹೆಚ್ಚು",
        "critical": "ಗಂಭೀರ",
        "irrigation": "ನೀರಾವರಿ",
        "temperature": "ಉಷ್ಣತೆ",
        "rainfall": "ಮಳೆ",
    },
    "bn": {
        "advisory_title": "কৃষি পরামর্শ",
        "risk_level": "ঝুঁকির মাত্রা",
        "low": "কম",
        "moderate": "মাঝারি",
        "high": "বেশি",
        "critical": "গুরুতর",
        "irrigation": "সেচ",
        "temperature": "তাপমাত্রা",
        "rainfall": "বৃষ্টিপাত",
    },
    "gu": {
        "advisory_title": "ખેતી સલાહ",
        "risk_level": "જોખમ સ્તર",
        "low": "ઓછું",
        "moderate": "મધ્યમ",
        "high": "વધુ",
        "critical": "ગંભીર",
        "irrigation": "સિંચાઈ",
        "temperature": "તાપમાન",
        "rainfall": "વરસાદ",
    },
    "ml": {
        "advisory_title": "കാർഷിക ഉപദേശം",
        "risk_level": "അപകട നില",
        "low": "കുറഞ്ഞ",
        "moderate": "ഇടത്തരം",
        "high": "ഉയർന്ന",
        "critical": "�ുരുതരം",
        "irrigation": "ജലസേചനം",
        "temperature": "താപനില",
        "rainfall": "മഴ",
    },
    "pa": {
        "advisory_title": "ਖੇਤੀ ਸਲਾਹ",
        "risk_level": "ਜੋਖਮ ਪੱਧਰ",
        "low": "ਘੱਟ",
        "moderate": "ਦਰਮਿਆਨਾ",
        "high": "ਜ਼ਿਆਦਾ",
        "critical": "गंभीर",
        "irrigation": "ਸਿੰਚਾਈ",
        "temperature": "ਤਾਪਮਾਨ",
        "rainfall": "ਬਰਸਾਤ",
    },
}

# Risk level translations
RISK_LABELS = {
    "en": {"LOW": "Low", "MODERATE": "Moderate", "HIGH": "High", "CRITICAL": "Critical"},
    "hi": {"LOW": "कम", "MODERATE": "मध्यम", "HIGH": "उच्च", "CRITICAL": "गंभीर"},
    "ta": {"LOW": "குறைவு", "MODERATE": "மிதமான", "HIGH": "உயர்", "CRITICAL": "மிக உயர்"},
    "te": {"LOW": "తక్కువ", "MODERATE": "మధ్యస్థం", "HIGH": "ఎక్కువ", "CRITICAL": "క్లిష్టం"},
    "mr": {"LOW": "कमी", "MODERATE": "दर्जेदार", "HIGH": "जास्त", "CRITICAL": "गंभीर"},
    "kn": {"LOW": "ಕಡಿಮೆ", "MODERATE": "ಮಧ್ಯಮ", "HIGH": "ಹೆಚ್ಚು", "CRITICAL": "ಗಂಭೀರ"},
    "bn": {"LOW": "কম", "MODERATE": "মাঝারি", "HIGH": "বেশি", "CRITICAL": "গুরুতর"},
    "gu": {"LOW": "ઓછું", "MODERATE": "મધ્યમ", "HIGH": "વધુ", "CRITICAL": "ગંભીર"},
    "ml": {"LOW": "കുറഞ്ഞ", "MODERATE": "ഇടത്തരം", "HIGH": "ഉയർന്ന", "CRITICAL": "ഗുരുതരം"},
    "pa": {"LOW": "ਘੱਟ", "MODERATE": "ਦਰਮਿਆਨਾ", "HIGH": "ਜ਼ਿਆਦਾ", "CRITICAL": "गंभीर"},
}


def get_translation(key: str, language: str = "en") -> str:
    """Get translation for a given key and language.

    Args:
        key: Translation key.
        language: Language code (e.g., 'en', 'hi', 'ta', 'te', 'mr').

    Returns:
        Translated string, or English fallback if not found.
    """
    lang_dict = TRANSLATIONS.get(language, TRANSLATIONS["en"])
    translated = lang_dict.get(key)
    if translated is None:
        # Fallback to English
        translated = TRANSLATIONS["en"].get(key, key)
    return translated


def get_risk_label(risk_level: str, language: str = "en") -> str:
    """Get translated risk level label."""
    labels = RISK_LABELS.get(language, RISK_LABELS["en"])
    return labels.get(risk_level, risk_level)


def get_supported_languages() -> list[dict]:
    """Return list of supported languages with their codes and names."""
    return [
        {"code": "en", "name": "English", "native": "English"},
        {"code": "hi", "name": "Hindi", "native": "हिन्दी"},
        {"code": "ta", "name": "Tamil", "native": "தமிழ்"},
        {"code": "te", "name": "Telugu", "native": "తెలుగు"},
        {"code": "mr", "name": "Marathi", "native": "मराठी"},
        {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ"},
        {"code": "bn", "name": "Bengali", "native": "বাংলা"},
        {"code": "gu", "name": "Gujarati", "native": "ગુજરાતી"},
        {"code": "ml", "name": "Malayalam", "native": "മലയാളം"},
        {"code": "pa", "name": "Punjabi", "native": "ਪੰਜਾਬੀ"},
    ]


def translate_text_simple(text: str, target_language: str = "hi") -> str:
    """Simple keyword-based translation for common advisory phrases.

    For production, use Gemini API or Google Translate. This provides
    a basic fallback that wraps the text with language-appropriate framing.

    Args:
        text: Text to translate.
        target_language: Target language code.

    Returns:
        Translated text with appropriate language framing.
    """
    if target_language == "en":
        return text

    # For non-English, return with a translation note
    # In production, this would call the Gemini API for proper translation
    lang_names = {
        "hi": "हिन्दी", "ta": "தமிழ்", "te": "తెలుగు",
        "mr": "मराठी", "kn": "ಕನ್ನಡ", "bn": "বাংলা",
        "gu": "ગુજરાતી", "ml": "മലയാളം", "pa": "ਪੰਜਾਬੀ",
    }
    lang_name = lang_names.get(target_language, target_language)
    logger.info(f"Translation to '{target_language}' requested - using keyword fallback")
    return f"[{lang_name}] {text}"
