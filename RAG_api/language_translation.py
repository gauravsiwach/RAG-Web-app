"""
language_translation.py

Handles multi-language support by translating user queries to English
before RAG processing, then translating responses back to user's language.

This layer allows the RAG system to work with English vectors only,
while supporting queries and responses in 100+ languages.
"""

import os
from typing import Tuple
from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.text import TextTranslationClient
from azure.core.exceptions import HttpResponseError

# Azure Translator Configuration
TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY")
TRANSLATOR_ENDPOINT = os.getenv("AZURE_TRANSLATOR_ENDPOINT")
TRANSLATOR_REGION = os.getenv("AZURE_TRANSLATOR_REGION")

# Initialize Azure Translator Client using SDK
translator_client = TextTranslationClient(
    credential=AzureKeyCredential(TRANSLATOR_KEY),
    region=TRANSLATOR_REGION
)

# Supported languages mapping (Hindi and English only)
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
}


def detect_language(text: str) -> str:
    """
    Detect the language of the input text using Azure Translator SDK.
    """
    try:
        # Use translate with auto-detect (do not set from_language)
        response = translator_client.translate(
            body=[text],
            to_language=["en"],
        )
        detected_lang = response[0].detected_language.language if response and response[0].detected_language else "en"
        confidence = response[0].detected_language.score if response and response[0].detected_language else 0
        print(f"🌍 Detected language: {detected_lang} (confidence: {confidence:.2f})")
        return detected_lang
    except HttpResponseError as e:
        print(f"❌ Error detecting language: {e.error.message if e.error else str(e)}")
        return "en"
    except Exception as e:
        print(f"❌ Error detecting language: {e}")
        return "en"
    

def translate_to_english(text: str, source_lang: str = None) -> Tuple[str, str]:
    """
    Translate text to English for RAG processing using Azure Translator SDK.
    
    Args:
        text: Text to translate
        source_lang: Source language code (auto-detected if None)
        
    Returns:
        Tuple of (translated_text, original_language)
    """
    try:
        # Auto-detect if not provided
        if source_lang is None:
            source_lang = detect_language(text)
        
        # If already English, return as-is
        if source_lang == "en":
            print(f"✅ Text already in English, no translation needed")
            return text, source_lang
        
        # Translate to English
        response = translator_client.translate(
            body=[text],
            to_language=["en"],
            from_language=source_lang
        )
        
        if response and len(response) > 0:
            translated_text = response[0].translations[0].text if response[0].translations else text
            
            print(f"🔄 Translated {source_lang} → en")
            print(f"   Original: {text[:100]}...")
            print(f"   Translated: {translated_text[:100]}...")
            
            return translated_text, source_lang
        else:
            print(f"⚠️ Translation returned empty response")
            return text, source_lang
            
    except HttpResponseError as e:
        print(f"❌ Error translating to English: {e.error.message if e.error else str(e)}")
        return text, source_lang or "en"
    except Exception as e:
        print(f"❌ Error translating to English: {e}")
        return text, source_lang or "en"


def translate_from_english(text: str, target_lang: str) -> str:
    """
    Translate English text back to user's language using Azure Translator SDK.
    
    Args:
        text: English text to translate
        target_lang: Target language code
        
    Returns:
        Translated text
    """
    try:
        # If target is English, return as-is
        if target_lang == "en":
            return text
        
        # Translate from English to target language
        response = translator_client.translate(
            body=[text],
            to_language=target_lang,
            from_language="en"
        )
        
        if response and len(response) > 0:
            translated_text = response[0].translations[0].text if response[0].translations else text
            
            print(f"🔄 Translated en → {target_lang}")
            print(f"   Original: {text[:100]}...")
            print(f"   Translated: {translated_text[:100]}...")
            
            return translated_text
        else:
            print(f"⚠️ Translation returned empty response")
            return text
            
    except HttpResponseError as e:
        print(f"❌ Error translating from English: {e.error.message if e.error else str(e)}")
        return text
    except Exception as e:
        print(f"❌ Error translating from English: {e}")
        return text


def process_multilingual_query(query: str) -> Tuple[str, str]:
    """
    Process user query for multi-language support.
    
    Detects language and translates to English if needed.
    
    Args:
        query: User query in any language
        
    Returns:
        Tuple of (english_query, original_language)
    """
    print(f"\n🌐 Processing multi-language query...")
    
    # Detect language
    detected_lang = detect_language(query)
    
    # Translate to English if needed
    english_query, original_lang = translate_to_english(query, detected_lang)
    
    return english_query, original_lang


def process_multilingual_response(response: str, target_lang: str) -> str:
    """
    Translate RAG response back to user's language.
    
    Args:
        response: English response from RAG system
        target_lang: Target language code
        
    Returns:
        Translated response
    """
    print(f"\n🌐 Translating response to {target_lang}...")
    
    translated_response = translate_from_english(response, target_lang)
    
    return translated_response


def get_supported_languages() -> dict:
    """
    Get list of supported languages.
    
    Returns:
        Dictionary of language codes and names
    """
    return SUPPORTED_LANGUAGES


def validate_language_code(lang_code: str) -> bool:
    """
    Validate if language code is supported.
    
    Args:
        lang_code: Language code to validate
        
    Returns:
        True if supported, False otherwise
    """
    return lang_code in SUPPORTED_LANGUAGES or lang_code.split("-")[0] in SUPPORTED_LANGUAGES
