"""
Interview Framework Library
Meridian HR Intelligence — Pure Technology

Structured interview questions with scoring rubrics by role category.
Implements Pure Method 2.0 interview methodology:
- Behavioral questions (past performance predicts future)
- Situational questions (how they'd handle scenarios)
- Values alignment (Pure Technology 7 pillars)
- Brilliance indicators (signs of potential, not just competence)
"""

from dataclasses import dataclass
from typing import Optional
import json
import os


@dataclass
class InterviewQuestion:
    """A single structured interview question."""
    id: str
    question: str
    category: str  # "behavioral", "situational", "values", "technical", "brilliance"
    pillar: str  # Which PT pillar it maps to (if values question)
    what_to_listen_for: list  # Scoring guidance
    red_flags: list
    green_flags: list
    follow_ups: list  # Probing questions
    scoring_rubric: dict  # 1-5 scale descriptions


@dataclass
class InterviewGuide:
    """Complete interview guide for a role."""
    job_title: str
    role_category: str
    total_time_minutes: int
    questions: list
    opening_script: str
    closing_script: str
    evaluation_criteria: dict

    def to_dict(self):
        return {
            "job_title": self.job_title,
            "role_category": self.role_category,
            "total_time_minutes": self.total_time_minutes,
            "question_count": len(self.questions),
            "questions": [
                {
                    "id": q.id,
                    "question": q.question,
                    "category": q.category,
                    "pillar": q.pillar,
                    "what_to_listen_for": q.what_to_listen_for,
                    "red_flags": q.red_flags,
                    "green_flags": q.green_flags,
                    "follow_ups": q.follow_ups,
                    "scoring_rubric": q.scoring_rubric,
                }
                for q in self.questions
            ],
            "opening_script": self.opening_script,
            "closing_script": self.closing_script,
            "evaluation_criteria": self.evaluation_criteria,
        }


class InterviewFramework:
    """
    Generates structured interview guides based on role category.

    Role Categories:
    - executive: C-suite, VP, Director
    - management: Manager, Team Lead, Supervisor
    - professional: Individual contributor, specialist
    - technical: Engineer, developer, architect
    - sales: Sales, business development, account management
    - operations: Operations, administration, support
    - entry: Junior, associate, intern
    """

    # Core question bank — maps category to questions
    CORE_QUESTIONS = {
        "behavioral": [
            InterviewQuestion(
                id="BH-001",
                question="Tell me about a time you had to deliver difficult feedback to someone. What was the situation, what did you say, and what happened?",
                category="behavioral",
                pillar="Transparency",
                what_to_listen_for=["Specific example", "How they framed the feedback", "Outcome and learning"],
                red_flags=["Avoided giving feedback", "Blamed others", "No specific example"],
                green_flags=["Direct but compassionate", "Prepared in advance", "Followed up after"],
                follow_ups=["How did you prepare for that conversation?", "Would you handle it differently now?"],
                scoring_rubric={
                    "1": "Cannot provide example or avoided feedback entirely",
                    "2": "Gave feedback but poorly — no preparation, harsh delivery",
                    "3": "Adequate — gave feedback with reasonable approach",
                    "4": "Strong — prepared, direct, compassionate, good outcome",
                    "5": "Exceptional — turned difficult conversation into growth moment for both parties",
                },
            ),
            InterviewQuestion(
                id="BH-002",
                question="Describe a project or initiative that failed. What was your role, what went wrong, and what did you learn?",
                category="behavioral",
                pillar="Accountability",
                what_to_listen_for=["Ownership vs blame", "Self-awareness", "Concrete learnings applied later"],
                red_flags=["Blames team/circumstances", "No reflection", "Claims no failures"],
                green_flags=["Takes ownership", "Shows vulnerability", "Applied learnings to future work"],
                follow_ups=["What would you do differently?", "How has that failure shaped your approach since?"],
                scoring_rubric={
                    "1": "Denies failures or blames everyone else",
                    "2": "Acknowledges failure but minimal reflection",
                    "3": "Describes failure with some ownership and learning",
                    "4": "Full ownership, clear learnings, evidence of applying them",
                    "5": "Transforms failure into a compelling growth narrative with proof of changed behavior",
                },
            ),
            InterviewQuestion(
                id="BH-003",
                question="Tell me about a time you went above and beyond for a colleague, customer, or teammate — not because you had to, but because you wanted to.",
                category="behavioral",
                pillar="Love",
                what_to_listen_for=["Intrinsic motivation", "Impact on others", "Whether it's genuine or performative"],
                red_flags=["Can't think of one", "Clearly performative", "Expects recognition for it"],
                green_flags=["Natural, unforced generosity", "Didn't expect anything in return", "Others-focused"],
                follow_ups=["What motivated you to do that?", "How did it make you feel?"],
                scoring_rubric={
                    "1": "Cannot provide an example",
                    "2": "Example feels transactional or forced",
                    "3": "Genuine effort but limited impact",
                    "4": "Meaningful act with clear positive impact",
                    "5": "Deeply generous, selfless, had lasting impact — reveals character",
                },
            ),
        ],
        "situational": [
            InterviewQuestion(
                id="ST-001",
                question="You discover that a popular team member is consistently underperforming but their team covers for them. How would you handle this?",
                category="situational",
                pillar="Integrity",
                what_to_listen_for=["Willingness to address", "Fairness to all parties", "Process-oriented thinking"],
                red_flags=["Would ignore it", "Would fire immediately", "Only cares about popularity"],
                green_flags=["Investigates root cause", "Has direct conversation", "Balances empathy with accountability"],
                follow_ups=["What if the person gets defensive?", "How would you handle the team dynamic?"],
                scoring_rubric={
                    "1": "Would avoid the situation entirely",
                    "2": "Would address but poorly — too harsh or too soft",
                    "3": "Reasonable approach with some gaps",
                    "4": "Balanced — investigates, addresses directly, considers team impact",
                    "5": "Masterful — addresses performance while preserving dignity and team trust",
                },
            ),
            InterviewQuestion(
                id="ST-002",
                question="Your team is given a project with an impossible deadline. You know quality will suffer if you rush. What do you do?",
                category="situational",
                pillar="Persistence",
                what_to_listen_for=["Problem-solving approach", "Communication skills", "Prioritization ability"],
                red_flags=["Just works harder with no pushback", "Gives up immediately", "Blames leadership"],
                green_flags=["Quantifies the tradeoff", "Proposes alternatives", "Communicates transparently upward"],
                follow_ups=["What if leadership says the deadline is non-negotiable?", "How do you decide what to cut?"],
                scoring_rubric={
                    "1": "No strategy — either complains or blindly complies",
                    "2": "Recognizes the problem but weak on solutions",
                    "3": "Proposes reasonable alternatives",
                    "4": "Strong analysis of tradeoffs, clear communication plan",
                    "5": "Creative problem-solving that finds a path others wouldn't see",
                },
            ),
        ],
        "values": [
            InterviewQuestion(
                id="VL-001",
                question="What does integrity mean to you in the workplace? Can you give me an example of when you had to choose between what was easy and what was right?",
                category="values",
                pillar="Integrity",
                what_to_listen_for=["Personal definition matches PT values", "Concrete example", "Cost of doing right"],
                red_flags=["Abstract answer with no example", "Integrity defined as 'following rules'"],
                green_flags=["Deeply personal", "Chose right over easy at personal cost", "No hesitation"],
                follow_ups=["What was the hardest part of that choice?", "How did others react?"],
                scoring_rubric={
                    "1": "Cannot articulate or provide example",
                    "2": "Generic definition, weak example",
                    "3": "Reasonable definition with decent example",
                    "4": "Strong personal definition backed by meaningful example",
                    "5": "Integrity is clearly a core operating principle — lived, not stated",
                },
            ),
            InterviewQuestion(
                id="VL-002",
                question="Pure Technology's vision is 'a brighter world where all people actualize their brilliance.' What does 'actualizing your brilliance' mean to you personally?",
                category="values",
                pillar="Growth",
                what_to_listen_for=["Self-awareness about strengths", "Growth mindset", "Connection to PT's mission"],
                red_flags=["Doesn't resonate", "Purely career-advancement focused", "No self-reflection"],
                green_flags=["Deeply reflective", "Connects personal growth to helping others grow", "Gets energized"],
                follow_ups=["What's your brilliance?", "What's stopping you from fully actualizing it?"],
                scoring_rubric={
                    "1": "Question doesn't land — no connection to the concept",
                    "2": "Surface-level answer focused on career goals",
                    "3": "Thoughtful reflection on personal growth",
                    "4": "Deep self-awareness + connection to helping others actualize",
                    "5": "Answer reveals someone who will embody PT's vision — you feel it",
                },
            ),
        ],
        "brilliance": [
            InterviewQuestion(
                id="BR-001",
                question="What's something you've taught yourself that nobody asked you to learn? Why did you learn it?",
                category="brilliance",
                pillar="Innovation",
                what_to_listen_for=["Intrinsic curiosity", "Self-directed learning", "How they apply it"],
                red_flags=["Can't think of anything", "Only learns when required", "Learns for credentials only"],
                green_flags=["Genuine curiosity", "Applied learning to real problems", "Still learning"],
                follow_ups=["How did you go about learning it?", "Have you taught anyone else?"],
                scoring_rubric={
                    "1": "No self-directed learning evident",
                    "2": "Minor self-study, credential-driven",
                    "3": "Genuine interest in learning, reasonable depth",
                    "4": "Strong self-directed learner, applies knowledge creatively",
                    "5": "Insatiable learner — the kind of person who makes everyone around them smarter",
                },
            ),
            InterviewQuestion(
                id="BR-002",
                question="If you could redesign any part of your current or last company, what would you change and why?",
                category="brilliance",
                pillar="Innovation",
                what_to_listen_for=["Systems thinking", "Constructive criticism", "Feasibility of ideas"],
                red_flags=["Only complaints, no solutions", "Says 'nothing' — not engaged enough to notice"],
                green_flags=["Identifies real systemic issue", "Has thought-out solution", "Shows they care"],
                follow_ups=["Did you ever propose this?", "What held the company back from doing it?"],
                scoring_rubric={
                    "1": "No ideas or only superficial complaints",
                    "2": "Identifies issues but solutions are weak",
                    "3": "Solid observation with reasonable improvement idea",
                    "4": "Insightful systems-level thinking with practical solution",
                    "5": "Reveals strategic thinker who sees what others miss — hire signal",
                },
            ),
        ],
    }

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path

    def generate_guide(
        self,
        job_title: str,
        role_category: str,
        focus_areas: Optional[list] = None,
        time_minutes: int = 60,
        custom_questions: Optional[list] = None,
    ) -> InterviewGuide:
        """
        Generate a structured interview guide.

        Args:
            job_title: The position title
            role_category: One of: executive, management, professional, technical, sales, operations, entry
            focus_areas: Optional list of question categories to emphasize
            time_minutes: Total interview time
            custom_questions: Optional list of additional InterviewQuestion objects
        """
        questions = self._select_questions(role_category, focus_areas, time_minutes)

        if custom_questions:
            questions.extend(custom_questions)

        opening = self._opening_script(job_title, time_minutes)
        closing = self._closing_script(job_title)
        criteria = self._evaluation_criteria(role_category)

        return InterviewGuide(
            job_title=job_title,
            role_category=role_category,
            total_time_minutes=time_minutes,
            questions=questions,
            opening_script=opening,
            closing_script=closing,
            evaluation_criteria=criteria,
        )

    def _select_questions(self, role_category: str, focus_areas: Optional[list], time_minutes: int) -> list:
        """Select appropriate questions based on role and time constraints."""
        # Estimate ~8 minutes per question (question + response + follow-up)
        max_questions = max(3, time_minutes // 8)

        # Category mix by role type
        category_mix = {
            "executive": {"behavioral": 2, "situational": 1, "values": 2, "brilliance": 1},
            "management": {"behavioral": 2, "situational": 2, "values": 1, "brilliance": 1},
            "professional": {"behavioral": 2, "situational": 1, "values": 1, "brilliance": 1},
            "technical": {"behavioral": 1, "situational": 1, "values": 1, "brilliance": 2},
            "sales": {"behavioral": 2, "situational": 2, "values": 1, "brilliance": 1},
            "operations": {"behavioral": 2, "situational": 1, "values": 1, "brilliance": 1},
            "entry": {"behavioral": 1, "situational": 1, "values": 2, "brilliance": 2},
        }

        mix = category_mix.get(role_category, category_mix["professional"])

        # Override with focus areas if provided
        if focus_areas:
            mix = {cat: (3 if cat in focus_areas else 1) for cat in mix}

        selected = []
        for category, count in mix.items():
            available = self.CORE_QUESTIONS.get(category, [])
            selected.extend(available[:count])

        return selected[:max_questions]

    def _opening_script(self, job_title: str, time_minutes: int) -> str:
        return (
            f"Thank you for taking the time to meet with us today. "
            f"We're excited to learn more about you and explore whether the {job_title} role "
            f"could be a great mutual fit. We have about {time_minutes} minutes together. "
            f"I'll ask you some questions, and please take your time with your answers — "
            f"we're interested in real examples and honest reflection, not rehearsed responses. "
            f"We'll save time at the end for your questions too. Sound good?"
        )

    def _closing_script(self, job_title: str) -> str:
        return (
            f"Thank you for your thoughtful answers. Before we wrap up — "
            f"what questions do you have for us about the {job_title} role, the team, "
            f"or Pure Technology? [After Q&A] We'll be in touch about next steps. "
            f"We appreciate you sharing your experiences with us today."
        )

    def _evaluation_criteria(self, role_category: str) -> dict:
        """Define what 'strong hire' looks like for each role type."""
        base = {
            "minimum_average_score": 3.5,
            "no_score_below": 2,
            "must_score_4_plus_on": ["values"],
            "decision_framework": {
                "strong_hire": "Average 4.0+, no score below 3, values questions all 4+",
                "hire": "Average 3.5+, no score below 2, at least one values question 4+",
                "maybe": "Average 3.0-3.5, investigate gaps before deciding",
                "no_hire": "Average below 3.0, or any critical red flag triggered",
            },
        }

        if role_category == "executive":
            base["must_score_4_plus_on"].extend(["situational", "brilliance"])
        elif role_category == "technical":
            base["must_score_4_plus_on"].append("brilliance")
        elif role_category == "entry":
            base["minimum_average_score"] = 3.0
            base["no_score_below"] = 1

        return base
