"""
Slide Intelligence Module - Enhanced content analysis and slide type recognition
"""

import re
from typing import Dict, List, Tuple, Optional
from enum import Enum

class SlideType(Enum):
    """Enumeration of slide types for adaptive content generation."""
    TITLE = "title"
    INTRO = "introduction"
    AGENDA = "agenda"
    CONTENT = "content"
    DATA_VISUAL = "data_visual"
    COMPARISON = "comparison"
    TRANSITION = "transition"
    SUMMARY = "summary"
    CONCLUSION = "conclusion"
    CALL_TO_ACTION = "call_to_action"
    APPENDIX = "appendix"
    QA = "questions"

class SlideAnalyzer:
    """Analyzes slides to determine type and extract intelligent insights."""
    
    def __init__(self):
        # Keywords that indicate different slide types
        self.type_indicators = {
            SlideType.TITLE: [
                r"^\s*slide\s*1\s*:",
                r"title\s*slide",
                r"presentation\s*title"
            ],
            SlideType.INTRO: [
                r"introduction",
                r"intro\b",
                r"overview",
                r"welcome",
                r"about\s+(us|this|our)"
            ],
            SlideType.AGENDA: [
                r"agenda",
                r"outline",
                r"today.?s\s+(topics|discussion)",
                r"table\s*of\s*contents",
                r"what\s*we.?ll\s*cover"
            ],
            SlideType.DATA_VISUAL: [
                r"chart",
                r"graph",
                r"table",
                r"figure\s*\d+",
                r"data",
                r"statistics",
                r"metrics",
                r"%|percent",
                r"growth\s*rate",
                r"market\s*size"
            ],
            SlideType.COMPARISON: [
                r"vs\.?|versus",
                r"comparison",
                r"compare",
                r"difference",
                r"advantages?\s*(and|&)\s*disadvantages?"
            ],
            SlideType.TRANSITION: [
                r"now\s*let.?s",
                r"moving\s*(on|forward)",
                r"next",
                r"turning\s*to",
                r"shift\s*(our\s*)?focus"
            ],
            SlideType.SUMMARY: [
                r"summary",
                r"recap",
                r"key\s*(points|takeaways)",
                r"in\s*summary",
                r"to\s*summarize"
            ],
            SlideType.CONCLUSION: [
                r"conclusion",
                r"conclud",
                r"final\s*thoughts",
                r"wrap\s*up",
                r"closing"
            ],
            SlideType.CALL_TO_ACTION: [
                r"next\s*steps",
                r"action\s*items",
                r"recommendations",
                r"what\s*you\s*can\s*do",
                r"call\s*to\s*action"
            ],
            SlideType.APPENDIX: [
                r"appendix",
                r"additional\s*information",
                r"reference",
                r"backup\s*slides"
            ],
            SlideType.QA: [
                r"questions\??",
                r"q\s*&\s*a",
                r"discussion",
                r"thank\s*you"
            ]
        }
        
        # Visual analysis patterns
        self.visual_patterns = {
            'trend': [
                r"increase",
                r"decrease",
                r"growth",
                r"decline",
                r"rise",
                r"fall",
                r"trend",
                r"trajectory"
            ],
            'comparison': [
                r"higher\s*than",
                r"lower\s*than",
                r"compared\s*to",
                r"versus",
                r"outperform",
                r"underperform"
            ],
            'outlier': [
                r"significant",
                r"notable",
                r"exception",
                r"unusual",
                r"spike",
                r"anomaly"
            ]
        }
    
    def identify_slide_type(self, slide_title: str, slide_content: str = "", slide_number: int = 1) -> SlideType:
        """
        Identifies the type of slide based on title, content, and position.
        
        Args:
            slide_title: The title or description of the slide
            slide_content: Additional content from the slide (optional)
            slide_number: The slide number
            
        Returns:
            SlideType enum value
        """
        combined_text = f"{slide_title} {slide_content}".lower()
        
        # Check slide 1 - usually title slide
        if slide_number == 1:
            return SlideType.TITLE
        
        # Check each type's indicators
        type_scores = {}
        for slide_type, patterns in self.type_indicators.items():
            score = sum(1 for pattern in patterns if re.search(pattern, combined_text, re.IGNORECASE))
            if score > 0:
                type_scores[slide_type] = score
        
        # Return the type with highest score, default to CONTENT
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        
        return SlideType.CONTENT
    
    def extract_data_insights(self, visual_description: str) -> Dict[str, List[str]]:
        """
        Extracts intelligent insights from visual descriptions.
        
        Args:
            visual_description: Description of charts, graphs, or data
            
        Returns:
            Dictionary of insight categories and findings
        """
        insights = {
            'trends': [],
            'comparisons': [],
            'outliers': [],
            'key_findings': []
        }
        
        lines = visual_description.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # Check for trends
            for pattern in self.visual_patterns['trend']:
                if re.search(pattern, line_lower):
                    insights['trends'].append(line.strip())
                    break
            
            # Check for comparisons
            for pattern in self.visual_patterns['comparison']:
                if re.search(pattern, line_lower):
                    insights['comparisons'].append(line.strip())
                    break
            
            # Check for outliers
            for pattern in self.visual_patterns['outlier']:
                if re.search(pattern, line_lower):
                    insights['outliers'].append(line.strip())
                    break
            
            # Extract key statistics (numbers with context)
            stat_pattern = r'\b\d+\.?\d*\s*%?.*?(growth|increase|decrease|market|share|rate)'
            if re.search(stat_pattern, line_lower):
                insights['key_findings'].append(line.strip())
        
        return insights
    
    def get_adaptive_structure(self, slide_type: SlideType, verbosity: str = "Standard") -> Dict[str, any]:
        """
        Returns an adaptive note structure based on slide type and verbosity.
        
        Args:
            slide_type: The identified type of slide
            verbosity: Level of detail (Brief, Standard, Detailed)
            
        Returns:
            Dictionary with structure guidelines
        """
        structures = {
            SlideType.TITLE: {
                "Brief": {
                    "bullets": 1,
                    "focus": ["Company/topic name", "Key theme"],
                    "template": ["Introducing [topic] - [key value proposition]"]
                },
                "Standard": {
                    "bullets": 2,
                    "focus": ["Introduction", "Context"],
                    "template": [
                        "Welcome audience and introduce [topic]",
                        "Frame the discussion around [key theme/challenge]"
                    ]
                },
                "Detailed": {
                    "bullets": 3,
                    "focus": ["Introduction", "Context", "Preview"],
                    "template": [
                        "Welcome and establish credibility on [topic]",
                        "Set context: [current situation/challenge]",
                        "Preview: We'll explore [main points]"
                    ]
                }
            },
            SlideType.DATA_VISUAL: {
                "Brief": {
                    "bullets": 2,
                    "focus": ["Key stat", "Implication"],
                    "template": [
                        "[Main data point] shows [trend/finding]",
                        "This means [business impact]"
                    ]
                },
                "Standard": {
                    "bullets": 3,
                    "focus": ["Data highlight", "Insight", "Action"],
                    "template": [
                        "The data reveals [key finding with number]",
                        "This [confirms/challenges] our understanding of [topic]",
                        "Implication: [what this means for strategy]"
                    ]
                },
                "Detailed": {
                    "bullets": 4,
                    "focus": ["Context", "Data", "Analysis", "Implications"],
                    "template": [
                        "Context: [Why this data matters]",
                        "Key finding: [Specific numbers and trends]",
                        "Notable: [Outliers or comparisons]",
                        "Strategic implication: [How this shapes decisions]"
                    ]
                }
            },
            SlideType.COMPARISON: {
                "Brief": {
                    "bullets": 2,
                    "focus": ["Winner", "Key differentiator"],
                    "template": [
                        "[Option A] outperforms with [key metric]",
                        "Main advantage: [differentiator]"
                    ]
                },
                "Standard": {
                    "bullets": 3,
                    "focus": ["Overview", "Key differences", "Recommendation"],
                    "template": [
                        "Comparing [A] vs [B] on [criteria]",
                        "Key difference: [A] excels at [X], while [B] offers [Y]",
                        "For our needs, [recommendation] because [reason]"
                    ]
                },
                "Detailed": {
                    "bullets": 4,
                    "focus": ["Setup", "Strengths", "Trade-offs", "Decision"],
                    "template": [
                        "We're evaluating [options] based on [criteria]",
                        "[A] strengths: [list], [B] strengths: [list]",
                        "Trade-offs to consider: [key considerations]",
                        "Recommendation: [choice] aligns with [strategic priority]"
                    ]
                }
            },
            SlideType.CONCLUSION: {
                "Brief": {
                    "bullets": 2,
                    "focus": ["Main takeaway", "Next step"],
                    "template": [
                        "Key insight: [main finding/recommendation]",
                        "Next: [immediate action]"
                    ]
                },
                "Standard": {
                    "bullets": 3,
                    "focus": ["Recap", "Conclusion", "Call to action"],
                    "template": [
                        "We've seen [key points recap]",
                        "This leads us to conclude [main insight]",
                        "Moving forward: [specific next steps]"
                    ]
                },
                "Detailed": {
                    "bullets": 4,
                    "focus": ["Journey", "Insights", "Implications", "Actions"],
                    "template": [
                        "Our analysis covered [main topics]",
                        "Key insights: [top 2-3 findings]",
                        "This means [strategic implications]",
                        "Recommended actions: [prioritized next steps]"
                    ]
                }
            }
        }
        
        # Default structure for content slides
        default_structure = {
            "Brief": {
                "bullets": 2,
                "focus": ["Main point", "Why it matters"],
                "template": [
                    "[Key message]",
                    "[Impact/relevance]"
                ]
            },
            "Standard": {
                "bullets": 3,
                "focus": ["Point", "Evidence", "Implication"],
                "template": [
                    "[Main message]",
                    "[Supporting evidence/example]",
                    "[What this means for audience]"
                ]
            },
            "Detailed": {
                "bullets": 4,
                "focus": ["Context", "Point", "Support", "Application"],
                "template": [
                    "[Setup/context]",
                    "[Main point]",
                    "[Evidence/examples]",
                    "[How to apply/next steps]"
                ]
            }
        }
        
        return structures.get(slide_type, default_structure).get(verbosity, default_structure["Standard"])
    
    def generate_storytelling_transition(self, from_type: SlideType, to_type: SlideType) -> str:
        """
        Generates appropriate transition phrases between slide types.
        
        Args:
            from_type: Current slide type
            to_type: Next slide type
            
        Returns:
            Transition phrase
        """
        transitions = {
            (SlideType.INTRO, SlideType.CONTENT): "Now let's dive into the details...",
            (SlideType.CONTENT, SlideType.DATA_VISUAL): "Let me show you what the data reveals...",
            (SlideType.DATA_VISUAL, SlideType.CONTENT): "These numbers tell us something important...",
            (SlideType.CONTENT, SlideType.COMPARISON): "To put this in perspective, let's compare...",
            (SlideType.COMPARISON, SlideType.CONTENT): "Based on this comparison...",
            (SlideType.CONTENT, SlideType.CONCLUSION): "This brings us to our key takeaways...",
            (SlideType.CONCLUSION, SlideType.CALL_TO_ACTION): "So what does this mean for you?",
            (SlideType.CONTENT, SlideType.CONTENT): "Building on this point...",
            (SlideType.DATA_VISUAL, SlideType.DATA_VISUAL): "Here's another important data point..."
        }
        
        return transitions.get((from_type, to_type), "Moving to our next topic...")

# Utility functions for integration
def analyze_presentation_intelligence(outline: str, visuals: str) -> Dict[int, Dict]:
    """
    Analyzes entire presentation for intelligent insights.
    
    Args:
        outline: Presentation outline text
        visuals: Visual analysis text
        
    Returns:
        Dictionary mapping slide numbers to intelligence data
    """
    analyzer = SlideAnalyzer()
    intelligence = {}
    
    # Parse outline
    slide_pattern = r'Slide\s+(\d+):\s*(.+?)(?=Slide\s+\d+:|$)'
    slides = re.findall(slide_pattern, outline, re.IGNORECASE | re.DOTALL)
    
    for i, (slide_num, slide_title) in enumerate(slides):
        slide_num = int(slide_num)
        
        # Get visual content for this slide if available
        visual_content = ""
        visual_pattern = f'Slide\\s+{slide_num}:.*?(?=Slide\\s+\\d+:|$)'
        visual_match = re.search(visual_pattern, visuals, re.IGNORECASE | re.DOTALL)
        if visual_match:
            visual_content = visual_match.group(0)
        
        # Identify slide type
        slide_type = analyzer.identify_slide_type(slide_title, visual_content, slide_num)
        
        # Extract insights if it's a data slide
        insights = {}
        if slide_type == SlideType.DATA_VISUAL and visual_content:
            insights = analyzer.extract_data_insights(visual_content)
        
        intelligence[slide_num] = {
            'title': slide_title.strip(),
            'type': slide_type,
            'insights': insights,
            'has_visual': bool(visual_content)
        }
    
    return intelligence

def format_intelligent_notes(slide_num: int, slide_intel: Dict, verbosity: str, 
                           prev_slide_type: Optional[SlideType] = None) -> str:
    """
    Formats speaker notes with intelligence.
    
    Args:
        slide_num: Slide number
        slide_intel: Intelligence data for the slide
        verbosity: Verbosity level
        prev_slide_type: Type of previous slide for transitions
        
    Returns:
        Formatted speaker notes
    """
    analyzer = SlideAnalyzer()
    slide_type = slide_intel['type']
    structure = analyzer.get_adaptive_structure(slide_type, verbosity)
    
    notes = [f"Slide {slide_num}: {slide_intel['title']}"]
    
    # Add transition if applicable
    if prev_slide_type and prev_slide_type != slide_type:
        transition = analyzer.generate_storytelling_transition(prev_slide_type, slide_type)
        notes.append(f"• (Transition) {transition}")
    
    # Add structured notes based on template
    for i, template in enumerate(structure['template']):
        notes.append(f"• {template}")
    
    # Add insights for data slides
    if slide_intel['insights'] and any(slide_intel['insights'].values()):
        if slide_intel['insights'].get('trends'):
            notes.append(f"• Key trend: {slide_intel['insights']['trends'][0]}")
        if slide_intel['insights'].get('outliers'):
            notes.append(f"• Notable: {slide_intel['insights']['outliers'][0]}")
    
    return '\n'.join(notes)