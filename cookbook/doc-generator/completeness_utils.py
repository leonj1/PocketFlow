import re
import math
from typing import Dict, List, Tuple, Set
from collections import defaultdict
import json

class ReadabilityAnalyzer:
    """Analyzes text readability using various metrics"""
    
    def __init__(self):
        self.audience_levels = {
            "beginner": {"flesch_kincaid": (0, 8), "flesch_ease": (60, 100)},
            "intermediate": {"flesch_kincaid": (6, 12), "flesch_ease": (30, 70)},
            "advanced": {"flesch_kincaid": (10, 16), "flesch_ease": (0, 50)},
            "expert": {"flesch_kincaid": (14, 20), "flesch_ease": (0, 30)}
        }
    
    def analyze_text(self, text: str) -> Dict:
        """Perform comprehensive readability analysis"""
        sentences = self._count_sentences(text)
        words = self._count_words(text)
        syllables = self._count_syllables(text)
        
        # Calculate metrics
        flesch_ease = self._flesch_reading_ease(sentences, words, syllables)
        flesch_kincaid = self._flesch_kincaid_grade(sentences, words, syllables)
        
        return {
            "word_count": words,
            "sentence_count": sentences,
            "avg_words_per_sentence": words / max(sentences, 1),
            "flesch_ease": flesch_ease,
            "flesch_kincaid_grade": flesch_kincaid,
            "complexity_level": self._determine_complexity(flesch_kincaid)
        }
    
    def check_audience_match(self, text: str, target_audience: str) -> Dict:
        """Check if text complexity matches target audience"""
        analysis = self.analyze_text(text)
        audience_key = self._map_audience_to_level(target_audience)
        
        if audience_key not in self.audience_levels:
            return {"match": True, "message": "Unknown audience level"}
        
        expected_range = self.audience_levels[audience_key]
        fk_grade = analysis["flesch_kincaid_grade"]
        
        fk_min, fk_max = expected_range["flesch_kincaid"]
        
        if fk_grade < fk_min:
            return {
                "match": False,
                "message": f"Text is too simple for {target_audience} audience. "
                          f"Flesch-Kincaid Grade: {fk_grade:.1f} (expected {fk_min}-{fk_max})",
                "suggestion": "Consider adding more technical depth and complexity."
            }
        elif fk_grade > fk_max:
            return {
                "match": False,
                "message": f"Text is too complex for {target_audience} audience. "
                          f"Flesch-Kincaid Grade: {fk_grade:.1f} (expected {fk_min}-{fk_max})",
                "suggestion": "Consider simplifying language and breaking down complex sentences."
            }
        
        return {
            "match": True,
            "message": f"Text complexity matches {target_audience} audience.",
            "grade": fk_grade
        }
    
    def _count_sentences(self, text: str) -> int:
        """Count sentences in text"""
        # Simple sentence counting - periods, exclamations, questions
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])
    
    def _count_words(self, text: str) -> int:
        """Count words in text"""
        words = re.findall(r'\b\w+\b', text)
        return len(words)
    
    def _count_syllables(self, text: str) -> int:
        """Estimate syllable count"""
        words = re.findall(r'\b\w+\b', text.lower())
        total_syllables = 0
        
        for word in words:
            # Simple syllable estimation
            vowels = re.findall(r'[aeiou]', word)
            syllables = len(vowels)
            
            # Adjust for common patterns
            if word.endswith('e'):
                syllables -= 1
            if re.search(r'[aeiou]{2}', word):
                syllables -= 1
            
            total_syllables += max(syllables, 1)
        
        return total_syllables
    
    def _flesch_reading_ease(self, sentences: int, words: int, syllables: int) -> float:
        """Calculate Flesch Reading Ease score"""
        if sentences == 0 or words == 0:
            return 0
        
        avg_sentence_length = words / sentences
        avg_syllables_per_word = syllables / words
        
        score = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word
        return max(0, min(100, score))
    
    def _flesch_kincaid_grade(self, sentences: int, words: int, syllables: int) -> float:
        """Calculate Flesch-Kincaid Grade Level"""
        if sentences == 0 or words == 0:
            return 0
        
        avg_sentence_length = words / sentences
        avg_syllables_per_word = syllables / words
        
        grade = 0.39 * avg_sentence_length + 11.8 * avg_syllables_per_word - 15.59
        return max(0, grade)
    
    def _determine_complexity(self, fk_grade: float) -> str:
        """Determine complexity level from Flesch-Kincaid grade"""
        if fk_grade < 6:
            return "elementary"
        elif fk_grade < 9:
            return "middle_school"
        elif fk_grade < 13:
            return "high_school"
        elif fk_grade < 16:
            return "college"
        else:
            return "graduate"
    
    def _map_audience_to_level(self, audience: str) -> str:
        """Map audience descriptors to complexity levels"""
        audience_lower = audience.lower()
        
        if any(term in audience_lower for term in ["beginner", "junior", "entry"]):
            return "beginner"
        elif any(term in audience_lower for term in ["mid", "intermediate"]):
            return "intermediate"
        elif any(term in audience_lower for term in ["senior", "advanced"]):
            return "advanced"
        elif any(term in audience_lower for term in ["expert", "principal", "lead"]):
            return "expert"
        
        return "intermediate"  # Default


class ConceptualGraphBuilder:
    """Builds and analyzes conceptual relationships in documents"""
    
    def __init__(self, terminology: List[Dict] = None):
        self.terminology = {term["term"]: term["definition"] for term in (terminology or [])}
        self.concept_graph = defaultdict(set)
        self.concept_contexts = defaultdict(list)
    
    def extract_concepts(self, text: str, section_name: str = None) -> Set[str]:
        """Extract key concepts from text"""
        concepts = set()
        
        # Extract defined terminology
        for term in self.terminology:
            if re.search(rf'\b{re.escape(term)}\b', text, re.IGNORECASE):
                concepts.add(term)
                self.concept_contexts[term].append({
                    "section": section_name,
                    "context": self._get_context(text, term)
                })
        
        # Extract other potential concepts (capitalized phrases, technical terms)
        # Pattern for multi-word technical terms
        technical_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b',  # Multi-word capitals
            r'\b\w+(?:API|SDK|URL|URI|ID|JWT|XML|JSON)\b',  # Technical suffixes
            r'\b(?:API|SDK|URL|URI|ID|JWT|XML|JSON)\w+\b',  # Technical prefixes
        ]
        
        for pattern in technical_patterns:
            matches = re.findall(pattern, text)
            concepts.update(matches)
        
        return concepts
    
    def build_relationships(self, text: str, concepts: Set[str]) -> None:
        """Build relationships between concepts based on proximity and context"""
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence_concepts = []
            for concept in concepts:
                if re.search(rf'\b{re.escape(concept)}\b', sentence, re.IGNORECASE):
                    sentence_concepts.append(concept)
            
            # Link concepts that appear in the same sentence
            for i, concept1 in enumerate(sentence_concepts):
                for concept2 in sentence_concepts[i+1:]:
                    self.concept_graph[concept1].add(concept2)
                    self.concept_graph[concept2].add(concept1)
    
    def analyze_conceptual_gaps(self) -> List[Dict]:
        """Identify conceptual gaps and disconnected concepts"""
        gaps = []
        
        # Find orphaned concepts (mentioned but not connected)
        all_concepts = set(self.concept_graph.keys()) | set().union(*self.concept_graph.values())
        
        for concept in all_concepts:
            if concept not in self.concept_graph or len(self.concept_graph[concept]) == 0:
                gaps.append({
                    "type": "orphaned_concept",
                    "concept": concept,
                    "message": f"The concept '{concept}' is mentioned but not connected to other concepts.",
                    "suggestion": f"Explain how '{concept}' relates to other key concepts in the document."
                })
        
        # Find undefined terminology usage
        for concept in all_concepts:
            if concept not in self.terminology and self._looks_like_terminology(concept):
                gaps.append({
                    "type": "undefined_term",
                    "concept": concept,
                    "message": f"The term '{concept}' is used but not defined in the terminology section.",
                    "suggestion": f"Add a definition for '{concept}' or link it to existing terminology."
                })
        
        # Find critical missing relationships
        critical_pairs = [
            ("API Key", "Authentication"),
            ("JWT", "Authorization"),
            ("OAuth", "User Consent"),
            ("Rate Limiting", "API Security")
        ]
        
        for concept1, concept2 in critical_pairs:
            if (concept1 in all_concepts and concept2 in all_concepts and
                concept2 not in self.concept_graph.get(concept1, set())):
                gaps.append({
                    "type": "missing_relationship",
                    "concepts": [concept1, concept2],
                    "message": f"'{concept1}' and '{concept2}' should be connected but aren't.",
                    "suggestion": f"Explain the relationship between '{concept1}' and '{concept2}'."
                })
        
        return gaps
    
    def _get_context(self, text: str, term: str, window: int = 50) -> str:
        """Get surrounding context for a term"""
        pattern = rf'(.{{0,{window}}}\b{re.escape(term)}\b.{{0,{window}}})'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1) if match else ""
    
    def _looks_like_terminology(self, concept: str) -> bool:
        """Check if a concept looks like technical terminology"""
        # Technical patterns that suggest terminology
        patterns = [
            r'^[A-Z]{2,}$',  # All caps abbreviations
            r'\b\w+(?:API|SDK|Auth|Token|Key)\b',  # Technical suffixes
            r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$',  # Title Case Phrases
        ]
        
        return any(re.match(pattern, concept) for pattern in patterns)


class GoalTracker:
    """Tracks document goals and their fulfillment"""
    
    def __init__(self, context: Dict):
        self.purpose = context.get("purpose", "")
        self.scope = context.get("scope", {})
        self.deliverables = context.get("deliverables", [])
        self.success_criteria = context.get("success_criteria", {})
        self.goals = self._extract_goals()
    
    def _extract_goals(self) -> List[Dict]:
        """Extract specific goals from context"""
        goals = []
        
        # Extract from purpose
        purpose_goals = self._parse_purpose_goals(self.purpose)
        goals.extend(purpose_goals)
        
        # Extract from scope includes
        if "includes" in self.scope:
            for item in self.scope["includes"]:
                goals.append({
                    "id": f"scope_{len(goals)}",
                    "description": item,
                    "type": "scope_requirement",
                    "fulfilled": False
                })
        
        # Extract from deliverable sections
        for deliverable in self.deliverables:
            if "sections" in deliverable:
                for section in deliverable["sections"]:
                    goals.append({
                        "id": f"section_{section['name']}",
                        "description": f"Complete '{section['name']}' section",
                        "type": "section_completion",
                        "section": section["name"],
                        "fulfilled": False
                    })
        
        return goals
    
    def _parse_purpose_goals(self, purpose: str) -> List[Dict]:
        """Parse goals from purpose statement"""
        goals = []
        
        # Look for action verbs that indicate goals
        action_patterns = [
            r'(?:to\s+)?(prevent|ensure|provide|implement|create|establish|define)\s+([^.]+)',
            r'(?:will\s+)(require|track|enforce|monitor)\s+([^.]+)',
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, purpose, re.IGNORECASE)
            for action, objective in matches:
                goals.append({
                    "id": f"purpose_{len(goals)}",
                    "description": f"{action.capitalize()} {objective.strip()}",
                    "type": "purpose_goal",
                    "action": action,
                    "objective": objective.strip(),
                    "fulfilled": False
                })
        
        return goals
    
    def check_goal_fulfillment(self, content: str, section_name: str = None) -> Dict:
        """Check which goals are fulfilled by the content"""
        fulfilled_goals = []
        unfulfilled_goals = []
        
        for goal in self.goals:
            if goal["type"] == "section_completion" and section_name:
                if goal["section"] == section_name and content.strip():
                    goal["fulfilled"] = True
                    fulfilled_goals.append(goal)
                    continue
            
            # Check if goal keywords appear in content
            if self._is_goal_addressed(goal, content):
                goal["fulfilled"] = True
                fulfilled_goals.append(goal)
            else:
                unfulfilled_goals.append(goal)
        
        return {
            "fulfilled": fulfilled_goals,
            "unfulfilled": unfulfilled_goals,
            "fulfillment_rate": len(fulfilled_goals) / max(len(self.goals), 1)
        }
    
    def _is_goal_addressed(self, goal: Dict, content: str) -> bool:
        """Check if a goal is addressed in the content"""
        # Extract key terms from goal description
        key_terms = re.findall(r'\b\w{4,}\b', goal["description"].lower())
        
        # Check if enough key terms appear in content
        content_lower = content.lower()
        matches = sum(1 for term in key_terms if term in content_lower)
        
        return matches >= len(key_terms) * 0.6  # 60% threshold


class ScopeComplianceChecker:
    """Checks if content stays within defined scope"""
    
    def __init__(self, context: Dict):
        self.includes = set(context.get("scope", {}).get("includes", []))
        self.excludes = set(context.get("scope", {}).get("out_of_scope", []))
        self.document_type = context.get("document_type", "")
    
    def check_scope_compliance(self, content: str, section_name: str = None) -> List[Dict]:
        """Check for scope violations"""
        violations = []
        
        # Check for out-of-scope content
        for excluded_topic in self.excludes:
            if self._topic_is_covered(excluded_topic, content):
                violations.append({
                    "type": "scope_creep",
                    "section": section_name,
                    "topic": excluded_topic,
                    "message": f"Content covers '{excluded_topic}' which is explicitly out of scope.",
                    "suggestion": f"Remove content about '{excluded_topic}' or move to appropriate document."
                })
        
        # Check if content matches document type
        if not self._matches_document_type(content):
            violations.append({
                "type": "document_type_mismatch",
                "section": section_name,
                "message": f"Content doesn't match expected '{self.document_type}' format.",
                "suggestion": f"Adjust content to align with {self.document_type} conventions."
            })
        
        return violations
    
    def _topic_is_covered(self, topic: str, content: str) -> bool:
        """Check if a topic is substantially covered in content"""
        # Extract key terms from topic
        key_terms = re.findall(r'\b\w+\b', topic.lower())
        
        # Check for significant coverage (multiple mentions or dedicated section)
        content_lower = content.lower()
        
        # Count occurrences of key terms
        total_mentions = sum(len(re.findall(rf'\b{term}\b', content_lower)) for term in key_terms)
        
        # Check for section headers
        has_section = any(re.search(rf'#+\s*.*{term}', content_lower, re.MULTILINE) for term in key_terms)
        
        return total_mentions > 5 or has_section
    
    def _matches_document_type(self, content: str) -> bool:
        """Check if content matches expected document type patterns"""
        doc_type_patterns = {
            "Technical Standard": [
                r'(?i)must\s+\w+',  # Normative language
                r'(?i)shall\s+\w+',
                r'(?i)required\s+to',
                r'(?i)specification',
            ],
            "User Guide": [
                r'(?i)how\s+to',
                r'(?i)steps?\s*:',
                r'(?i)example',
                r'(?i)tutorial',
            ],
            "API Documentation": [
                r'(?i)endpoint',
                r'(?i)request.*response',
                r'(?i)parameter',
                r'(?i)return',
            ],
            "Architecture Document": [
                r'(?i)component',
                r'(?i)diagram',
                r'(?i)architecture',
                r'(?i)design\s+pattern',
            ]
        }
        
        patterns = doc_type_patterns.get(self.document_type, [])
        if not patterns:
            return True  # Unknown type, assume compliant
        
        # Check if enough patterns match
        matches = sum(1 for pattern in patterns if re.search(pattern, content))
        return matches >= len(patterns) * 0.5  # 50% threshold