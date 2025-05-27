"""
Language detection and multi-language support utilities
"""

import re
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class LanguageDetector:
    """Detects language of text and provides language-specific processing."""
    
    def __init__(self):
        # Common patterns for language detection
        self.language_patterns = {
            'chinese': {
                'chars': r'[\u4e00-\u9fff\u3400-\u4dbf]',  # CJK unified ideographs
                'threshold': 0.3,  # 30% Chinese characters
                'name': 'Chinese',
                'code': 'zh'
            },
            'japanese': {
                'chars': r'[\u3040-\u309f\u30a0-\u30ff]',  # Hiragana and Katakana
                'threshold': 0.1,
                'name': 'Japanese',
                'code': 'ja'
            },
            'korean': {
                'chars': r'[\uac00-\ud7af\u1100-\u11ff]',  # Hangul
                'threshold': 0.3,
                'name': 'Korean',
                'code': 'ko'
            },
            'arabic': {
                'chars': r'[\u0600-\u06ff\u0750-\u077f]',  # Arabic
                'threshold': 0.3,
                'name': 'Arabic',
                'code': 'ar'
            },
            'spanish': {
                'words': ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'por', 'para', 'está', 'pero', 'como'],
                'chars': r'[áéíóúñ¿¡]',
                'threshold': 0.01,
                'name': 'Spanish',
                'code': 'es'
            },
            'french': {
                'words': ['le', 'de', 'un', 'être', 'et', 'à', 'il', 'avoir', 'ne', 'je', 'vous', 'nous'],
                'chars': r'[àâçèéêëîïôùûü]',
                'threshold': 0.01,
                'name': 'French',
                'code': 'fr'
            },
            'german': {
                'words': ['der', 'das', 'ist', 'nicht', 'ich', 'wir', 'haben', 'werden', 'kann', 'auf', 'für', 'aber', 'noch', 'durch', 'muss', 'mehr', 'sehr', 'schon', 'beim', 'nach'],
                'chars': r'[äöüßÄÖÜ]',
                'threshold': 0.01,
                'name': 'German',
                'code': 'de'
            },
            'portuguese': {
                'words': ['o', 'de', 'e', 'a', 'em', 'para', 'que', 'com', 'não', 'uma', 'por', 'mais'],
                'chars': r'[áàâãçéêíóôõú]',
                'threshold': 0.01,
                'name': 'Portuguese',
                'code': 'pt'
            }
        }
        
        # Common English words to help distinguish from other languages
        self.english_indicators = [
            'the', 'is', 'are', 'was', 'were', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'this', 'that', 'these', 'those', 'what', 'which', 'who', 'when', 'where',
            'why', 'how', 'all', 'some', 'any', 'each', 'every', 'no', 'not',
            'can', 'cannot', "can't", 'just', 'only', 'also', 'very', 'really',
            'about', 'after', 'before', 'during', 'through', 'under', 'over',
            'between', 'among', 'from', 'with', 'without', 'within', 'into',
            'onto', 'upon', 'below', 'above', 'behind', 'beside', 'beneath',
            # Business and presentation-specific English words
            'presentation', 'slide', 'data', 'market', 'growth', 'business',
            'analysis', 'report', 'summary', 'overview', 'introduction', 'conclusion',
            'product', 'service', 'customer', 'revenue', 'profit', 'strategy',
            'performance', 'results', 'forecast', 'trend', 'opportunity', 'challenge'
        ]
    
    def detect_language(self, text: str) -> Tuple[str, str]:
        """
        Detects the primary language of the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (language_name, language_code)
        """
        if not text:
            return ('English', 'en')
        
        text_lower = text.lower()
        text_length = len(text)
        
        # Check for character-based languages first (Chinese, Japanese, Korean, Arabic)
        for lang, config in self.language_patterns.items():
            if 'chars' in config and lang in ['chinese', 'japanese', 'korean', 'arabic']:
                matches = len(re.findall(config['chars'], text))
                ratio = matches / text_length if text_length > 0 else 0
                
                if ratio >= config['threshold']:
                    logger.info(f"Detected {config['name']} language (ratio: {ratio:.2f})")
                    return (config['name'], config['code'])
        
        # For European languages, use more sophisticated detection
        # Count special characters specific to each language
        special_char_counts = {}
        for lang, config in self.language_patterns.items():
            if 'chars' in config and lang in ['spanish', 'french', 'german', 'portuguese']:
                special_matches = len(re.findall(config['chars'], text))
                char_ratio = special_matches / text_length if text_length > 0 else 0
                if char_ratio >= config['threshold']:
                    special_char_counts[lang] = char_ratio
        
        # If we have special characters, that's a strong indicator
        if special_char_counts:
            best_char_match = max(special_char_counts.items(), key=lambda x: x[1])
            config = self.language_patterns[best_char_match[0]]
            logger.info(f"Detected {config['name']} language based on special characters (ratio: {best_char_match[1]:.3f})")
            return (config['name'], config['code'])
        
        # Check for word-based language detection with higher threshold
        word_scores = {}
        english_score = 0
        words = text_lower.split()
        total_words = len(words)
        
        # Only check if we have enough text
        if total_words > 20:
            # Check English indicators first
            english_score = sum(1 for word in words if word in self.english_indicators)
            english_percentage = (english_score / total_words) * 100 if total_words > 0 else 0
            
            # Check other languages
            for lang, config in self.language_patterns.items():
                if 'words' in config:
                    # Count only words that are reasonably specific (at least 3 characters)
                    score = sum(1 for word in words if word in config['words'] and len(word) >= 3)
                    # Calculate percentage of matching words
                    word_percentage = (score / total_words) * 100 if total_words > 0 else 0
                    if word_percentage > 1.5:  # At least 1.5% of words match
                        word_scores[lang] = score
                        logger.debug(f"Language {config['name']}: {score} words matched ({word_percentage:.1f}%)")
        
        # Log all scores for debugging
        if word_scores or english_score > 0:
            logger.debug(f"Language detection scores - English: {english_score}, Others: {word_scores}")
        
        # If English has a strong presence, prefer it
        if english_percentage > 3.0:  # If more than 3% of words are common English words
            logger.info(f"Strong English indicators found ({english_score} words, {english_percentage:.1f}%)")
            return ('English', 'en')
        
        # If we have significant matches for a non-English language
        if word_scores:
            best_match = max(word_scores.items(), key=lambda x: x[1])
            # Require at least 7 common words AND higher percentage than English
            if best_match[1] >= 7 and (best_match[1] > english_score * 1.5):
                config = self.language_patterns[best_match[0]]
                logger.info(f"Detected {config['name']} language (word matches: {best_match[1]} vs English: {english_score})")
                return (config['name'], config['code'])
        
        # Default to English
        logger.info("Defaulting to English language")
        return ('English', 'en')
    
    def get_language_instructions(self, language_code: str) -> str:
        """
        Returns language-specific instructions for AI prompts.
        
        Args:
            language_code: ISO language code
            
        Returns:
            Instructions for maintaining language consistency
        """
        language_names = {
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'pt': 'Portuguese',
            'en': 'English'
        }
        
        language_name = language_names.get(language_code, 'English')
        
        if language_code == 'en':
            return ""  # No special instructions for English
        
        return f"""
IMPORTANT LANGUAGE REQUIREMENT:
The input content is in {language_name}. You MUST:
1. Maintain ALL output in {language_name}
2. Preserve the original language for all generated content
3. Do not translate to English unless explicitly requested
4. Use culturally appropriate expressions and formatting for {language_name}
5. Maintain proper {language_name} grammar and style conventions

All speaker notes, analysis, and insights must be written in {language_name}.
"""

    def adapt_prompt_for_language(self, prompt: str, language_code: str) -> str:
        """
        Adapts a prompt to include language-specific instructions.
        
        Args:
            prompt: Original prompt
            language_code: Detected language code
            
        Returns:
            Adapted prompt with language instructions
        """
        language_instructions = self.get_language_instructions(language_code)
        
        if language_instructions:
            # For prompts ending with "Presentation content:", insert before that
            if prompt.endswith("Presentation content:"):
                return prompt[:-20] + "\n" + language_instructions + "\n\nPresentation content:"
            
            # For vision prompts with {{InputDocument}}, insert after the placeholder
            elif "{{InputDocument}}" in prompt:
                # Find the first sentence or paragraph break after {{InputDocument}}
                # to insert the language instructions
                parts = prompt.split('\n', 1)
                if len(parts) == 2 and "{{InputDocument}}" in parts[0]:
                    # Insert after first line
                    return parts[0] + "\n" + language_instructions + "\n" + parts[1]
                else:
                    # Insert after the placeholder on the same line
                    return prompt.replace(
                        "{{InputDocument}}", 
                        "{{InputDocument}}" + "\n" + language_instructions + "\n"
                    )
            
            # For other prompts, insert at the beginning
            return language_instructions + "\n\n" + prompt
        
        return prompt

# Utility functions for prompt adaptation
def detect_and_adapt_prompts(deck_text: str, briefing_text: str = "") -> Dict[str, any]:
    """
    Detects language and returns adapted prompt configuration.
    
    Args:
        deck_text: Presentation deck text
        briefing_text: Optional briefing document text
        
    Returns:
        Dictionary with language info and adaptation instructions
    """
    detector = LanguageDetector()
    
    # Combine texts for better language detection
    combined_text = deck_text + "\n" + briefing_text
    
    language_name, language_code = detector.detect_language(combined_text)
    
    return {
        'language_name': language_name,
        'language_code': language_code,
        'instructions': detector.get_language_instructions(language_code),
        'detector': detector
    }

def enhance_prompt_with_language(prompt: str, language_info: Dict) -> str:
    """
    Enhances a prompt with language-specific instructions.
    
    Args:
        prompt: Original prompt
        language_info: Language detection results
        
    Returns:
        Enhanced prompt
    """
    if not language_info:
        return prompt
        
    if language_info.get('language_code') != 'en':
        try:
            enhanced = language_info['detector'].adapt_prompt_for_language(
                prompt, 
                language_info['language_code']
            )
            
            # Verify the enhancement didn't break required placeholders (only for vision prompts)
            if "{{InputDocument}}" in prompt and "{{InputDocument}}" not in enhanced:
                logger.error("Language enhancement removed {{InputDocument}} placeholder.")
                logger.debug(f"Original prompt: {prompt[:200]}...")
                logger.debug(f"Enhanced prompt: {enhanced[:200]}...")
                return prompt
                
            return enhanced
        except Exception as e:
            logger.error(f"Error enhancing prompt with language: {e}")
            return prompt
    return prompt