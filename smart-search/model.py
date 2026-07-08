"""
SMART SEARCH — Candidate-to-Job Description Scoring Engine
Meridian HR Intelligence — Pure Technology

Scores how well a candidate matches a job description across 8 dimensions.
Produces a weighted match score (0-100) with detailed breakdown.

SMART = Skills, Motivation, Alignment, Readiness, Trajectory
"""

from dataclasses import dataclass
from typing import Optional
import json
import os


@dataclass
class MatchDimension:
    """Score for a single matching dimension."""
    name: str
    score: float  # 0-100
    weight: float
    weighted_score: float
    evidence: list  # What justified this score
    gaps: list  # What's missing


@dataclass
class CandidateMatch:
    """Complete match assessment for a candidate against a JD."""
    candidate_name: str
    job_title: str
    overall_score: float
    match_tier: str  # "Strong Match", "Good Match", "Partial Match", "Weak Match"
    dimensions: list
    strengths: list
    gaps: list
    interview_focus: list  # What to probe in interview
    hiring_recommendation: str

    def to_dict(self):
        return {
            "candidate_name": self.candidate_name,
            "job_title": self.job_title,
            "overall_score": round(self.overall_score, 1),
            "match_tier": self.match_tier,
            "dimensions": [
                {
                    "name": d.name,
                    "score": round(d.score, 1),
                    "weight": d.weight,
                    "evidence": d.evidence,
                    "gaps": d.gaps,
                }
                for d in self.dimensions
            ],
            "strengths": self.strengths,
            "gaps": self.gaps,
            "interview_focus": self.interview_focus,
            "hiring_recommendation": self.hiring_recommendation,
        }


class SmartSearchScorer:
    """
    Scores candidates against job descriptions using the SMART framework.

    8 Dimensions:
    1. Hard Skills Match — Technical/functional skills required
    2. Soft Skills Match — Communication, leadership, collaboration
    3. Experience Level — Years + depth of relevant experience
    4. Industry Alignment — Same or adjacent industry experience
    5. Education Fit — Degree/certification requirements
    6. Culture Indicators — Values alignment signals from resume
    7. Growth Trajectory — Career progression pattern
    8. Availability & Logistics — Location, start date, comp expectations
    """

    DEFAULT_WEIGHTS = {
        "hard_skills": 0.25,
        "soft_skills": 0.10,
        "experience_level": 0.20,
        "industry_alignment": 0.10,
        "education_fit": 0.08,
        "culture_indicators": 0.10,
        "growth_trajectory": 0.07,
        "availability_logistics": 0.10,
    }

    TIER_THRESHOLDS = [
        (85, "Strong Match"),
        (70, "Good Match"),
        (55, "Partial Match"),
        (0, "Weak Match"),
    ]

    def __init__(self, config_path: Optional[str] = None):
        self.weights = self.DEFAULT_WEIGHTS.copy()
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
                self.weights.update(config.get("weights", {}))

    def score_candidate(
        self,
        candidate_name: str,
        job_title: str,
        candidate_data: dict,
        jd_requirements: dict,
    ) -> CandidateMatch:
        """
        Score a candidate against job description requirements.

        Args:
            candidate_name: Candidate's name
            job_title: Job title being matched against
            candidate_data: Parsed candidate profile
                - skills: list of str (technical skills)
                - soft_skills: list of str
                - years_experience: int
                - industries: list of str
                - education: {"degree": str, "field": str, "certifications": list}
                - values_signals: list of str (from resume language)
                - career_moves: list of {"title": str, "duration_months": int}
                - location: str
                - comp_expectation: float (optional)
                - available_date: str (optional)

            jd_requirements: Parsed job description
                - required_skills: list of str
                - preferred_skills: list of str
                - required_soft_skills: list of str
                - min_experience: int (years)
                - preferred_experience: int (years)
                - target_industries: list of str
                - education_required: {"degree": str, "field": str}
                - certifications_required: list of str
                - culture_values: list of str
                - location: str
                - remote_ok: bool
                - comp_range: {"min": float, "max": float}

        Returns:
            CandidateMatch with detailed scoring
        """
        dimensions = []
        all_strengths = []
        all_gaps = []

        # 1. Hard Skills
        dim = self._score_hard_skills(candidate_data, jd_requirements)
        dimensions.append(dim)

        # 2. Soft Skills
        dim = self._score_soft_skills(candidate_data, jd_requirements)
        dimensions.append(dim)

        # 3. Experience Level
        dim = self._score_experience(candidate_data, jd_requirements)
        dimensions.append(dim)

        # 4. Industry Alignment
        dim = self._score_industry(candidate_data, jd_requirements)
        dimensions.append(dim)

        # 5. Education Fit
        dim = self._score_education(candidate_data, jd_requirements)
        dimensions.append(dim)

        # 6. Culture Indicators
        dim = self._score_culture(candidate_data, jd_requirements)
        dimensions.append(dim)

        # 7. Growth Trajectory
        dim = self._score_trajectory(candidate_data)
        dimensions.append(dim)

        # 8. Availability & Logistics
        dim = self._score_logistics(candidate_data, jd_requirements)
        dimensions.append(dim)

        # Collect strengths and gaps
        for d in dimensions:
            if d.score >= 80:
                all_strengths.extend(d.evidence[:2])
            all_gaps.extend(d.gaps)

        # Calculate overall
        overall = sum(
            d.score * self.weights.get(d.name, 0.1) for d in dimensions
        )
        tier = self._get_tier(overall)

        # Interview focus — probe the gaps
        interview_focus = []
        weak_dims = sorted(dimensions, key=lambda d: d.score)[:3]
        for d in weak_dims:
            if d.score < 70 and d.gaps:
                interview_focus.append(
                    f"Probe {d.name}: {d.gaps[0]}"
                )

        # Hiring recommendation
        recommendation = self._recommendation(overall, all_gaps, dimensions)

        return CandidateMatch(
            candidate_name=candidate_name,
            job_title=job_title,
            overall_score=overall,
            match_tier=tier,
            dimensions=dimensions,
            strengths=all_strengths[:5],
            gaps=all_gaps[:5],
            interview_focus=interview_focus[:3],
            hiring_recommendation=recommendation,
        )

    def _score_hard_skills(self, candidate: dict, jd: dict) -> MatchDimension:
        """Score technical/functional skill match."""
        cand_skills = set(s.lower() for s in candidate.get("skills", []))
        req_skills = set(s.lower() for s in jd.get("required_skills", []))
        pref_skills = set(s.lower() for s in jd.get("preferred_skills", []))

        if not req_skills:
            return MatchDimension("hard_skills", 70, self.weights["hard_skills"], 0, ["No required skills specified"], [])

        req_match = cand_skills & req_skills
        req_missing = req_skills - cand_skills
        pref_match = cand_skills & pref_skills

        # Score: required matches are worth 80%, preferred worth 20%
        req_pct = len(req_match) / len(req_skills) if req_skills else 1
        pref_pct = len(pref_match) / len(pref_skills) if pref_skills else 0.5
        score = min(100, (req_pct * 80) + (pref_pct * 20))

        evidence = [f"Matches {len(req_match)}/{len(req_skills)} required skills"]
        if pref_match:
            evidence.append(f"Also has {len(pref_match)} preferred skills: {', '.join(list(pref_match)[:3])}")

        gaps = []
        if req_missing:
            gaps.append(f"Missing required: {', '.join(list(req_missing)[:5])}")

        return MatchDimension("hard_skills", score, self.weights["hard_skills"], score * self.weights["hard_skills"], evidence, gaps)

    def _score_soft_skills(self, candidate: dict, jd: dict) -> MatchDimension:
        """Score soft skill alignment."""
        cand_soft = set(s.lower() for s in candidate.get("soft_skills", []))
        req_soft = set(s.lower() for s in jd.get("required_soft_skills", []))

        if not req_soft:
            return MatchDimension("soft_skills", 65, self.weights["soft_skills"], 0, ["No specific soft skills listed in JD"], [])

        matches = cand_soft & req_soft
        missing = req_soft - cand_soft
        score = min(100, (len(matches) / len(req_soft)) * 100) if req_soft else 65

        evidence = [f"Demonstrates {len(matches)}/{len(req_soft)} required soft skills"] if matches else []
        gaps = [f"Not demonstrated: {', '.join(list(missing)[:3])}"] if missing else []

        return MatchDimension("soft_skills", score, self.weights["soft_skills"], score * self.weights["soft_skills"], evidence, gaps)

    def _score_experience(self, candidate: dict, jd: dict) -> MatchDimension:
        """Score experience level match."""
        cand_years = candidate.get("years_experience", 0)
        min_req = jd.get("min_experience", 0)
        pref_req = jd.get("preferred_experience", min_req)

        evidence = []
        gaps = []

        if cand_years >= pref_req:
            score = 100
            evidence.append(f"{cand_years} years meets/exceeds preferred {pref_req}")
        elif cand_years >= min_req:
            score = 70 + (30 * (cand_years - min_req) / max(1, pref_req - min_req))
            evidence.append(f"{cand_years} years meets minimum {min_req}")
            gaps.append(f"Below preferred {pref_req} years")
        elif cand_years >= min_req * 0.7:
            score = 50
            gaps.append(f"{cand_years} years slightly below minimum {min_req}")
        else:
            score = max(10, 50 * (cand_years / max(1, min_req)))
            gaps.append(f"Significant experience gap: {cand_years} vs {min_req} required")

        return MatchDimension("experience_level", score, self.weights["experience_level"], score * self.weights["experience_level"], evidence, gaps)

    def _score_industry(self, candidate: dict, jd: dict) -> MatchDimension:
        """Score industry alignment."""
        cand_industries = set(i.lower() for i in candidate.get("industries", []))
        target = set(i.lower() for i in jd.get("target_industries", []))

        if not target:
            return MatchDimension("industry_alignment", 70, self.weights["industry_alignment"], 0, ["No industry preference specified"], [])

        direct_match = cand_industries & target
        if direct_match:
            score = 100
            evidence = [f"Direct industry match: {', '.join(direct_match)}"]
            gaps = []
        elif cand_industries:
            score = 50  # Adjacent industry — could be valuable
            evidence = [f"Different industry: {', '.join(list(cand_industries)[:2])}"]
            gaps = [f"No direct match to target: {', '.join(list(target)[:2])}"]
        else:
            score = 30
            evidence = []
            gaps = ["No industry information available"]

        return MatchDimension("industry_alignment", score, self.weights["industry_alignment"], score * self.weights["industry_alignment"], evidence, gaps)

    def _score_education(self, candidate: dict, jd: dict) -> MatchDimension:
        """Score education and certification fit."""
        cand_edu = candidate.get("education", {})
        req_edu = jd.get("education_required", {})
        req_certs = set(c.lower() for c in jd.get("certifications_required", []))
        cand_certs = set(c.lower() for c in cand_edu.get("certifications", []))

        evidence = []
        gaps = []
        score = 70  # Default — education is often flexible

        # Degree check
        if req_edu.get("degree"):
            degree_hierarchy = ["high school", "associate", "bachelor", "master", "phd", "doctorate"]
            cand_level = cand_edu.get("degree", "").lower()
            req_level = req_edu["degree"].lower()

            cand_idx = next((i for i, d in enumerate(degree_hierarchy) if d in cand_level), -1)
            req_idx = next((i for i, d in enumerate(degree_hierarchy) if d in req_level), -1)

            if cand_idx >= req_idx and cand_idx >= 0:
                score = 90
                evidence.append(f"Education meets requirement: {cand_edu.get('degree', 'N/A')}")
            elif cand_idx >= 0:
                score = 50
                gaps.append(f"Education below requirement: has {cand_edu.get('degree', 'N/A')}, needs {req_edu['degree']}")

        # Certification check
        if req_certs:
            cert_match = cand_certs & req_certs
            cert_missing = req_certs - cand_certs
            if cert_match:
                score = min(100, score + 10)
                evidence.append(f"Has certifications: {', '.join(cert_match)}")
            if cert_missing:
                score = max(30, score - 15)
                gaps.append(f"Missing certifications: {', '.join(cert_missing)}")

        return MatchDimension("education_fit", score, self.weights["education_fit"], score * self.weights["education_fit"], evidence, gaps)

    def _score_culture(self, candidate: dict, jd: dict) -> MatchDimension:
        """Score culture and values alignment signals."""
        cand_values = set(v.lower() for v in candidate.get("values_signals", []))
        company_values = set(v.lower() for v in jd.get("culture_values", []))

        if not company_values:
            return MatchDimension("culture_indicators", 60, self.weights["culture_indicators"], 0, ["No culture values specified in JD"], [])

        overlap = cand_values & company_values
        score = min(100, 40 + (60 * len(overlap) / len(company_values))) if company_values else 60

        evidence = [f"Values alignment on: {', '.join(overlap)}"] if overlap else []
        gaps = []
        if len(overlap) < len(company_values) * 0.5:
            gaps.append("Limited values alignment signals in resume")

        return MatchDimension("culture_indicators", score, self.weights["culture_indicators"], score * self.weights["culture_indicators"], evidence, gaps)

    def _score_trajectory(self, candidate: dict) -> MatchDimension:
        """Score career growth trajectory."""
        moves = candidate.get("career_moves", [])

        if not moves:
            return MatchDimension("growth_trajectory", 50, self.weights["growth_trajectory"], 0, ["No career history provided"], ["Cannot assess trajectory"])

        evidence = []
        gaps = []

        # Check for progression (titles getting more senior)
        if len(moves) >= 2:
            # Simple heuristic: longer tenures + increasing responsibility
            avg_tenure = sum(m.get("duration_months", 12) for m in moves) / len(moves)

            if avg_tenure >= 24:
                score = 80
                evidence.append(f"Stable tenure: avg {avg_tenure:.0f} months per role")
            elif avg_tenure >= 12:
                score = 60
                evidence.append(f"Moderate tenure: avg {avg_tenure:.0f} months per role")
            else:
                score = 35
                gaps.append(f"Short tenure pattern: avg {avg_tenure:.0f} months — flight risk")

            if len(moves) >= 3:
                score = min(100, score + 10)
                evidence.append(f"{len(moves)} career moves show progression")
        else:
            score = 55
            evidence.append("Limited career history — early career or single employer")

        return MatchDimension("growth_trajectory", score, self.weights["growth_trajectory"], score * self.weights["growth_trajectory"], evidence, gaps)

    def _score_logistics(self, candidate: dict, jd: dict) -> MatchDimension:
        """Score availability and logistical fit."""
        evidence = []
        gaps = []
        score = 70  # Default

        # Location check
        cand_loc = candidate.get("location", "").lower()
        jd_loc = jd.get("location", "").lower()
        remote_ok = jd.get("remote_ok", False)

        if remote_ok:
            score = 90
            evidence.append("Remote OK — location flexible")
        elif cand_loc and jd_loc and cand_loc == jd_loc:
            score = 90
            evidence.append(f"Location match: {cand_loc}")
        elif cand_loc and jd_loc:
            score = 50
            gaps.append(f"Location mismatch: candidate in {cand_loc}, role in {jd_loc}")

        # Comp check
        comp_range = jd.get("comp_range", {})
        cand_comp = candidate.get("comp_expectation")
        if comp_range and cand_comp:
            if comp_range.get("min", 0) <= cand_comp <= comp_range.get("max", float("inf")):
                score = min(100, score + 10)
                evidence.append("Comp expectation within range")
            elif cand_comp > comp_range.get("max", float("inf")):
                score = max(20, score - 30)
                gaps.append(f"Comp expectation ${cand_comp:,.0f} exceeds max ${comp_range['max']:,.0f}")

        return MatchDimension("availability_logistics", score, self.weights["availability_logistics"], score * self.weights["availability_logistics"], evidence, gaps)

    def _get_tier(self, score: float) -> str:
        for threshold, tier in self.TIER_THRESHOLDS:
            if score >= threshold:
                return tier
        return "Weak Match"

    def _recommendation(self, overall: float, gaps: list, dimensions: list) -> str:
        if overall >= 85:
            return "STRONG RECOMMEND — Advance to interview immediately. Top-tier match."
        elif overall >= 70:
            critical_gaps = [d for d in dimensions if d.score < 50 and d.weight >= 0.15]
            if critical_gaps:
                return f"CONDITIONAL — Good overall but probe: {critical_gaps[0].name} is weak."
            return "RECOMMEND — Solid match. Proceed to interview."
        elif overall >= 55:
            return "MAYBE — Partial match. Consider if candidate pool is limited or if gaps are trainable."
        else:
            return "PASS — Significant gaps. Only consider if role is hard to fill."
