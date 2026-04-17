"""
Voice Intelligence Service
Analyzes speech patterns, fluency, confidence, and communication quality
"""

import re
from typing import Dict, List
from collections import Counter

class VoiceAnalyzer:
    def __init__(self):
        self.filler_words = [
            'um', 'uh', 'like', 'you know', 'actually', 'basically', 
            'literally', 'sort of', 'kind of', 'i mean', 'well'
        ]
        
        self.confidence_indicators = {
            'high': ['definitely', 'certainly', 'absolutely', 'confident', 'sure'],
            'low': ['maybe', 'perhaps', 'i think', 'probably', 'not sure', 'i guess']
        }
    
    def analyze_speech(self, transcript: str, duration_seconds: float = None) -> Dict:
        """
        Comprehensive speech analysis
        
        Args:
            transcript: Speech-to-text transcript
            duration_seconds: Duration of speech in seconds
        
        Returns:
            {
                "fluency_score": 0-100,
                "confidence_score": 0-100,
                "clarity_score": 0-100,
                "words_per_minute": 150,
                "filler_word_count": 5,
                "filler_word_ratio": 0.03,
                "pause_indicators": 8,
                "sentence_structure_score": 75,
                "vocabulary_richness": 0.65,
                "feedback": "Detailed feedback",
                "strengths": [...],
                "improvements": [...]
            }
        """
        
        if not transcript or len(transcript.strip()) == 0:
            return self._empty_analysis()
        
        # Basic metrics
        words = transcript.split()
        word_count = len(words)
        unique_words = len(set(word.lower() for word in words))
        
        # Calculate WPM
        wpm = 0
        if duration_seconds and duration_seconds > 0:
            wpm = int((word_count / duration_seconds) * 60)
        
        # Filler word analysis
        filler_count = self._count_filler_words(transcript.lower())
        filler_ratio = filler_count / max(word_count, 1)
        
        # Pause indicators (multiple spaces, ellipsis, etc.)
        pause_count = len(re.findall(r'\.{2,}|  +|\.\.\.|--', transcript))
        
        # Confidence analysis
        confidence_score = self._analyze_confidence(transcript.lower())
        
        # Sentence structure
        sentences = [s.strip() for s in re.split(r'[.!?]+', transcript) if s.strip()]
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        sentence_structure_score = self._score_sentence_structure(avg_sentence_length)
        
        # Vocabulary richness (unique words / total words)
        vocabulary_richness = unique_words / max(word_count, 1)
        
        # Calculate scores
        fluency_score = self._calculate_fluency_score(wpm, filler_ratio, pause_count)
        clarity_score = self._calculate_clarity_score(sentence_structure_score, vocabulary_richness)
        
        # Generate feedback
        feedback_data = self._generate_feedback(
            fluency_score, confidence_score, clarity_score,
            wpm, filler_count, pause_count, vocabulary_richness
        )
        
        return {
            "fluency_score": round(fluency_score, 1),
            "confidence_score": round(confidence_score, 1),
            "clarity_score": round(clarity_score, 1),
            "overall_communication_score": round((fluency_score + confidence_score + clarity_score) / 3, 1),
            "words_per_minute": wpm,
            "word_count": word_count,
            "unique_word_count": unique_words,
            "filler_word_count": filler_count,
            "filler_word_ratio": round(filler_ratio * 100, 2),
            "pause_indicators": pause_count,
            "sentence_count": len(sentences),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "sentence_structure_score": round(sentence_structure_score, 1),
            "vocabulary_richness": round(vocabulary_richness * 100, 1),
            "feedback": feedback_data["feedback"],
            "strengths": feedback_data["strengths"],
            "improvements": feedback_data["improvements"],
            "detailed_analysis": {
                "pace": self._analyze_pace(wpm),
                "filler_words_used": self._get_filler_words_used(transcript.lower()),
                "confidence_indicators": self._get_confidence_indicators(transcript.lower())
            }
        }
    
    def _count_filler_words(self, text: str) -> int:
        """Count filler words in text"""
        count = 0
        for filler in self.filler_words:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(filler) + r'\b'
            count += len(re.findall(pattern, text))
        return count
    
    def _get_filler_words_used(self, text: str) -> List[Dict]:
        """Get list of filler words used with counts"""
        filler_usage = []
        for filler in self.filler_words:
            pattern = r'\b' + re.escape(filler) + r'\b'
            count = len(re.findall(pattern, text))
            if count > 0:
                filler_usage.append({"word": filler, "count": count})
        return sorted(filler_usage, key=lambda x: x["count"], reverse=True)
    
    def _analyze_confidence(self, text: str) -> float:
        """Analyze confidence level from text (0-100)"""
        high_count = sum(text.count(word) for word in self.confidence_indicators['high'])
        low_count = sum(text.count(word) for word in self.confidence_indicators['low'])
        
        total = high_count + low_count
        if total == 0:
            return 70  # Neutral
        
        confidence_ratio = high_count / total
        return 50 + (confidence_ratio * 50)  # Scale to 50-100
    
    def _get_confidence_indicators(self, text: str) -> Dict:
        """Get confidence indicators found in text"""
        high_found = [word for word in self.confidence_indicators['high'] if word in text]
        low_found = [word for word in self.confidence_indicators['low'] if word in text]
        
        return {
            "high_confidence": high_found,
            "low_confidence": low_found
        }
    
    def _score_sentence_structure(self, avg_length: float) -> float:
        """Score sentence structure (0-100)"""
        # Ideal sentence length: 15-20 words
        if 15 <= avg_length <= 20:
            return 100
        elif 10 <= avg_length < 15 or 20 < avg_length <= 25:
            return 80
        elif 5 <= avg_length < 10 or 25 < avg_length <= 30:
            return 60
        else:
            return 40
    
    def _calculate_fluency_score(self, wpm: int, filler_ratio: float, pause_count: int) -> float:
        """Calculate fluency score (0-100)"""
        score = 100
        
        # WPM scoring (ideal: 130-160)
        if wpm > 0:
            if wpm < 100:
                score -= min(30, (100 - wpm) / 2)
            elif wpm > 180:
                score -= min(30, (wpm - 180) / 2)
            elif 130 <= wpm <= 160:
                score += 0  # Perfect range
            else:
                score -= 5  # Slightly off
        
        # Filler word penalty
        if filler_ratio > 0.05:  # More than 5%
            score -= min(30, filler_ratio * 300)
        
        # Pause penalty
        if pause_count > 5:
            score -= min(20, (pause_count - 5) * 2)
        
        return max(0, min(100, score))
    
    def _calculate_clarity_score(self, sentence_score: float, vocab_richness: float) -> float:
        """Calculate clarity score (0-100)"""
        # Weight: 60% sentence structure, 40% vocabulary
        return (sentence_score * 0.6) + (vocab_richness * 100 * 0.4)
    
    def _analyze_pace(self, wpm: int) -> Dict:
        """Analyze speaking pace"""
        if wpm == 0:
            return {"rating": "unknown", "feedback": "No timing data available"}
        elif wpm < 100:
            return {"rating": "slow", "feedback": "Speaking pace is slow. Try to speak more confidently."}
        elif wpm > 180:
            return {"rating": "fast", "feedback": "Speaking pace is fast. Slow down for better clarity."}
        elif 130 <= wpm <= 160:
            return {"rating": "excellent", "feedback": "Perfect speaking pace!"}
        else:
            return {"rating": "good", "feedback": "Good speaking pace."}
    
    def _generate_feedback(
        self, fluency: float, confidence: float, clarity: float,
        wpm: int, filler_count: int, pause_count: int, vocab_richness: float
    ) -> Dict:
        """Generate comprehensive feedback"""
        
        strengths = []
        improvements = []
        
        # Fluency feedback
        if fluency >= 80:
            strengths.append("Excellent fluency and natural flow")
        elif fluency >= 60:
            strengths.append("Good fluency with minor hesitations")
        else:
            improvements.append("Practice speaking more fluently without long pauses")
        
        # Confidence feedback
        if confidence >= 75:
            strengths.append("Confident and assertive communication")
        elif confidence >= 60:
            strengths.append("Moderate confidence in responses")
        else:
            improvements.append("Use more confident language and avoid hedging words")
        
        # Clarity feedback
        if clarity >= 75:
            strengths.append("Clear and well-structured sentences")
        elif clarity >= 60:
            strengths.append("Generally clear communication")
        else:
            improvements.append("Improve sentence structure and vocabulary variety")
        
        # Specific metrics feedback
        if wpm > 0:
            if 130 <= wpm <= 160:
                strengths.append(f"Ideal speaking pace ({wpm} WPM)")
            elif wpm < 100:
                improvements.append(f"Increase speaking pace (currently {wpm} WPM, aim for 130-160)")
            elif wpm > 180:
                improvements.append(f"Slow down speaking pace (currently {wpm} WPM, aim for 130-160)")
        
        if filler_count > 5:
            improvements.append(f"Reduce filler words (detected {filler_count} instances)")
        elif filler_count <= 2:
            strengths.append("Minimal use of filler words")
        
        if pause_count > 8:
            improvements.append("Reduce excessive pauses for better flow")
        
        if vocab_richness >= 0.6:
            strengths.append("Rich and varied vocabulary")
        elif vocab_richness < 0.4:
            improvements.append("Use more varied vocabulary")
        
        # Generate summary feedback
        overall = (fluency + confidence + clarity) / 3
        
        if overall >= 80:
            summary = "Excellent communication skills! Your speech is fluent, confident, and clear."
        elif overall >= 65:
            summary = "Good communication skills with room for minor improvements."
        elif overall >= 50:
            summary = "Moderate communication skills. Focus on fluency and confidence."
        else:
            summary = "Communication skills need improvement. Practice speaking clearly and confidently."
        
        return {
            "feedback": summary,
            "strengths": strengths if strengths else ["Keep practicing to develop strengths"],
            "improvements": improvements if improvements else ["Continue maintaining good communication"]
        }
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis when no transcript available"""
        return {
            "fluency_score": 0,
            "confidence_score": 0,
            "clarity_score": 0,
            "overall_communication_score": 0,
            "words_per_minute": 0,
            "word_count": 0,
            "unique_word_count": 0,
            "filler_word_count": 0,
            "filler_word_ratio": 0,
            "pause_indicators": 0,
            "sentence_count": 0,
            "avg_sentence_length": 0,
            "sentence_structure_score": 0,
            "vocabulary_richness": 0,
            "feedback": "No speech data available for analysis",
            "strengths": [],
            "improvements": [],
            "detailed_analysis": {
                "pace": {"rating": "unknown", "feedback": "No data"},
                "filler_words_used": [],
                "confidence_indicators": {"high_confidence": [], "low_confidence": []}
            }
        }
    
    def compare_answers(self, answers: List[Dict]) -> Dict:
        """
        Compare multiple answers to show improvement trends
        
        Args:
            answers: List of {transcript, duration} dicts
        
        Returns:
            Trend analysis showing improvement over time
        """
        if not answers or len(answers) < 2:
            return {"error": "Need at least 2 answers to compare"}
        
        analyses = [self.analyze_speech(a.get('transcript', ''), a.get('duration')) for a in answers]
        
        # Calculate trends
        fluency_trend = [a['fluency_score'] for a in analyses]
        confidence_trend = [a['confidence_score'] for a in analyses]
        clarity_trend = [a['clarity_score'] for a in analyses]
        
        return {
            "answer_count": len(answers),
            "fluency_trend": fluency_trend,
            "confidence_trend": confidence_trend,
            "clarity_trend": clarity_trend,
            "average_fluency": sum(fluency_trend) / len(fluency_trend),
            "average_confidence": sum(confidence_trend) / len(confidence_trend),
            "average_clarity": sum(clarity_trend) / len(clarity_trend),
            "improvement": {
                "fluency": fluency_trend[-1] - fluency_trend[0],
                "confidence": confidence_trend[-1] - confidence_trend[0],
                "clarity": clarity_trend[-1] - clarity_trend[0]
            },
            "trend_direction": {
                "fluency": "improving" if fluency_trend[-1] > fluency_trend[0] else "declining",
                "confidence": "improving" if confidence_trend[-1] > confidence_trend[0] else "declining",
                "clarity": "improving" if clarity_trend[-1] > clarity_trend[0] else "declining"
            }
        }
