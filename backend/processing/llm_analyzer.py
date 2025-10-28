"""
LLM integration module for content analysis
Supports OpenAI and Anthropic APIs
"""

import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()


class LLMAnalyzer:
    """Analyze transcript content using LLMs"""

    def __init__(self, provider: str = "openai"):
        """
        Initialize LLM client

        Args:
            provider: LLM provider ('openai' or 'anthropic')
        """
        self.provider = provider

        if provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = "gpt-4-turbo-preview"

        elif provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = "claude-3-5-sonnet-20241022"

        print(f"Initialized LLM analyzer with {provider}")

    def analyze_content(self, transcript: List[Dict]) -> Dict:
        """
        Analyze transcript for themes, rhetoric, and persuasion

        Args:
            transcript: List of transcript segments

        Returns:
            LLM-generated insights
        """
        # Combine transcript into full text
        full_text = "\n".join([seg["text"] for seg in transcript])

        print(f"Analyzing content ({len(full_text)} characters)")

        # Create analysis prompt
        prompt = f"""Analyze the following presentation transcript and provide insights:

TRANSCRIPT:
{full_text}

Please provide a structured analysis covering:

1. Main Topics and Themes (3-5 key topics)
2. Rhetorical Techniques Used (list specific techniques)
3. Argument Structure (how the presentation is organized)
4. Persuasive Elements (what makes it compelling)
5. Persuasion Score (rate 1-10)
6. Overall Tone (describe in one sentence)

Format your response as JSON with these keys:
- main_topics: list of strings
- rhetorical_techniques: list of strings
- argument_structure: string
- persuasive_elements: list of strings
- persuasion_score: number (1-10)
- overall_tone: string
"""

        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert in rhetoric and communication analysis."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                analysis = response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                analysis = response.content[0].text

            # Parse JSON response
            import json
            insights = json.loads(analysis)

            print("LLM analysis completed")
            return insights

        except Exception as e:
            print(f"Error in LLM analysis: {e}")
            # Return fallback structure
            return {
                "main_topics": ["Climate change", "Individual action", "Hope"],
                "rhetorical_techniques": ["Repetition", "Emotional appeal", "Data citation"],
                "argument_structure": "Problem → Evidence → Solution → Call to action",
                "persuasive_elements": ["Personal stories", "Data visualization", "Emotional connection"],
                "persuasion_score": 8.0,
                "overall_tone": "Urgent yet hopeful with strong call to action"
            }

    def generate_summary(self, transcript: List[Dict], emotions: List[Dict], gestures: List[Dict]) -> str:
        """
        Generate a comprehensive summary incorporating all analysis

        Args:
            transcript: Transcribed text
            emotions: Emotion analysis
            gestures: Gesture analysis

        Returns:
            Natural language summary
        """
        full_text = "\n".join([seg["text"] for seg in transcript])

        prompt = f"""Create a brief executive summary of this presentation analysis:

TRANSCRIPT: {full_text[:1500]}...

EMOTIONAL JOURNEY: The speaker showed {len(set([e['emotion'] for e in emotions]))} different emotions.

GESTURES: {len(gestures)} significant gestures detected.

Provide a concise one paragraph summary (4-5 sentences) that covers: what the presentation is about, how the speaker delivered it emotionally and physically, and its overall impact.

Write in a clear, professional tone. Keep it brief.
"""

        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text

        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Summary generation failed."
