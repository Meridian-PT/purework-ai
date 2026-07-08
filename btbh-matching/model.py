"""
BTBH — Born To Be Hired Matching Engine
Meridian HR Intelligence — Pure Technology

Matches candidates to jobs using a weighted compatibility model.
Goes beyond SMART SEARCH by factoring in mutual fit — not just
"can they do the job" but "will both sides thrive?"

Philosophy: Pure Method 2.0 — "We don't hire people that are good enough.
We hire people we believe will actualize their brilliance."
"""

from dataclasses import dataclass
from typing import Optional
import json
import os


@dataclass
class MatchFactor:
    """A single factor in the BTBH match."""
    name: str
    category: str  # "capability", "motivation", "environment", "trajectory"
    score: float  # 0-100
    weight: float
    signal_strength: str  # "strong", "moderate", "weak", "inferred"
    evidence: str


@dataclass
class BTBHMatch:
    """Complete Born To Be Hired match result."""
    candidate_name: str
    job_title: str
    company_name: str
    overall_score: float
    match_verdict: str
    capability_score: float
    motivation_score: float
    environment_score: float
    trajectory_score: float
    factors: list
    deal_breakers: list
    brilliance_indicators: list  # Signs they'll "actualize their brilliance"
    mutual_fit_notes: list  # Why BOTH sides benefit

    def to_dict(self):
        return {
            "candidate_name": self.candidate_name,
            "job_title": self.job_title,
            "company_name": self.company_name,
            "overall_score": round(self.overall_score, 1),
            "match_verdict": self.match_verdict,
            "quadrant_scores": {
                "capability": round(self.capability_score, 1),
                "motivation": round(self.motivation_score, 1),
                "environment": round(self.environment_score, 1),
                "trajectory": round(self.trajectory_score, 1),
            },
            "deal_breakers": self.deal_breakers,
            "brilliance_indicators": self.brilliance_indicators,
            "mutual_fit_notes": self.mutual_fit_notes,
        }


class BTBHMatcher:
    """
    Four-quadrant matching model:

    1. CAPABILITY (Can they do it?)
       - Skills match, experience depth, domain knowledge

    2. MOTIVATION (Do they want it?)
       - Role interest signals, career goals alignment, comp fit

    3. ENVIRONMENT (Will they thrive here?)
       - Culture fit, management style, team dynamics, work arrangement

    4. TRAJECTORY (Will they grow with us?)
       - Learning velocity, ambition alignment, long-term potential

    A strong match requires ALL four quadrants above threshold.
    One weak quadrant = conditional match. Two weak = likely pass.
    """

    QUADRANT_WEIGHTS = {
        "capability": 0.30,
        "motivation": 0.25,
        "environment": 0.25,
        "trajectory": 0.20,
    }

    QUADRANT_MINIMUM = 40  # Below this in any quadrant = deal breaker

    VERDICT_MAP = [
        (90, "Born To Be Hired — exceptional mutual fit"),
        (80, "Strong Match — advance with confidence"),
        (70, "Good Match — worth pursuing"),
        (55, "Conditional — needs deeper assessment"),
        (0, "Not This Role — but maybe another"),
    ]

    def __init__(self, config_path: Optional[str] = None):
        self.config = {"quadrant_weights": self.QUADRANT_WEIGHTS.copy(), "quadrant_minimum": self.QUADRANT_MINIMUM}
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                self.config.update(json.load(f))

    def match(
        self,
        candidate_name: str,
        job_title: str,
        company_name: str,
        candidate_profile: dict,
        job_profile: dict,
        company_profile: dict,
    ) -> BTBHMatch:
        """
        Run the BTBH matching algorithm.

        Args:
            candidate_profile: {
                "skills": [...], "experience_years": int,
                "career_goals": str, "values": [...],
                "work_style": str, "growth_areas": [...],
                "comp_expectation": float, "motivators": [...]
            }
            job_profile: {
                "required_skills": [...], "min_experience": int,
                "growth_opportunities": [...], "team_size": int,
                "management_style": str, "remote_policy": str,
                "comp_range": {"min": float, "max": float}
            }
            company_profile: {
                "values": [...], "culture_traits": [...],
                "growth_stage": str, "reputation_score": float
            }
        """
        factors = []
        deal_breakers = []
        brilliance = []

        # Score each quadrant
        cap_factors, cap_score = self._score_capability(candidate_profile, job_profile)
        mot_factors, mot_score = self._score_motivation(candidate_profile, job_profile)
        env_factors, env_score = self._score_environment(candidate_profile, job_profile, company_profile)
        traj_factors, traj_score = self._score_trajectory(candidate_profile, job_profile)

        factors.extend(cap_factors + mot_factors + env_factors + traj_factors)

        # Check for deal breakers (any quadrant below minimum)
        min_threshold = self.config["quadrant_minimum"]
        quadrant_scores = {
            "capability": cap_score,
            "motivation": mot_score,
            "environment": env_score,
            "trajectory": traj_score,
        }
        for q_name, q_score in quadrant_scores.items():
            if q_score < min_threshold:
                deal_breakers.append(f"{q_name} score ({q_score:.0f}) below minimum threshold ({min_threshold})")

        # Calculate overall (weighted)
        weights = self.config["quadrant_weights"]
        overall = (
            cap_score * weights["capability"]
            + mot_score * weights["motivation"]
            + env_score * weights["environment"]
            + traj_score * weights["trajectory"]
        )

        # Penalty for deal breakers
        if deal_breakers:
            overall = min(overall, 55)  # Cap at Conditional if deal breakers exist

        # Identify brilliance indicators
        brilliance = self._find_brilliance(factors, quadrant_scores)

        # Mutual fit notes
        mutual_fit = self._assess_mutual_fit(candidate_profile, job_profile, company_profile, quadrant_scores)

        verdict = self._get_verdict(overall)

        return BTBHMatch(
            candidate_name=candidate_name,
            job_title=job_title,
            company_name=company_name,
            overall_score=overall,
            match_verdict=verdict,
            capability_score=cap_score,
            motivation_score=mot_score,
            environment_score=env_score,
            trajectory_score=traj_score,
            factors=factors,
            deal_breakers=deal_breakers,
            brilliance_indicators=brilliance,
            mutual_fit_notes=mutual_fit,
        )

    def _score_capability(self, candidate: dict, job: dict) -> tuple:
        """Score: Can they do the job?"""
        factors = []

        # Skills overlap
        cand_skills = set(s.lower() for s in candidate.get("skills", []))
        req_skills = set(s.lower() for s in job.get("required_skills", []))
        if req_skills:
            overlap = len(cand_skills & req_skills) / len(req_skills)
            skill_score = min(100, overlap * 100)
        else:
            skill_score = 60

        factors.append(MatchFactor(
            name="skills_overlap",
            category="capability",
            score=skill_score,
            weight=0.6,
            signal_strength="strong" if req_skills else "weak",
            evidence=f"{len(cand_skills & req_skills)}/{len(req_skills)} required skills matched" if req_skills else "No required skills specified",
        ))

        # Experience depth
        cand_years = candidate.get("experience_years", 0)
        min_exp = job.get("min_experience", 0)
        if min_exp > 0:
            exp_ratio = min(1.5, cand_years / max(1, min_exp))
            exp_score = min(100, exp_ratio * 70)
        else:
            exp_score = 70

        factors.append(MatchFactor(
            name="experience_depth",
            category="capability",
            score=exp_score,
            weight=0.4,
            signal_strength="strong",
            evidence=f"{cand_years} years vs {min_exp} required",
        ))

        overall = skill_score * 0.6 + exp_score * 0.4
        return factors, overall

    def _score_motivation(self, candidate: dict, job: dict) -> tuple:
        """Score: Do they actually want this?"""
        factors = []
        scores = []

        # Career goals alignment
        goals = candidate.get("career_goals", "")
        title = job.get("title", "")
        # Simple heuristic — real implementation would use NLP
        goal_score = 65  # Default moderate
        factors.append(MatchFactor(
            name="career_alignment",
            category="motivation",
            score=goal_score,
            weight=0.4,
            signal_strength="inferred",
            evidence=f"Career goals: {goals[:80]}..." if goals else "No career goals stated",
        ))
        scores.append(goal_score)

        # Comp fit
        comp_exp = candidate.get("comp_expectation", 0)
        comp_range = job.get("comp_range", {})
        if comp_exp and comp_range:
            comp_min = comp_range.get("min", 0)
            comp_max = comp_range.get("max", float("inf"))
            if comp_min <= comp_exp <= comp_max:
                comp_score = 90
                evidence = "Comp expectation within range"
            elif comp_exp < comp_min:
                comp_score = 75  # They'd take less — motivation concern?
                evidence = f"Expects below range (${comp_exp:,.0f} vs ${comp_min:,.0f}-${comp_max:,.0f})"
            else:
                comp_score = 30
                evidence = f"Expects above range (${comp_exp:,.0f} vs ${comp_max:,.0f} max)"
        else:
            comp_score = 60
            evidence = "Comp data incomplete"

        factors.append(MatchFactor(
            name="comp_alignment",
            category="motivation",
            score=comp_score,
            weight=0.3,
            signal_strength="strong" if (comp_exp and comp_range) else "weak",
            evidence=evidence,
        ))
        scores.append(comp_score)

        # Motivator alignment
        motivators = set(m.lower() for m in candidate.get("motivators", []))
        growth_opps = set(g.lower() for g in job.get("growth_opportunities", []))
        if motivators and growth_opps:
            mot_overlap = len(motivators & growth_opps) / max(1, len(motivators))
            mot_score = min(100, 40 + mot_overlap * 60)
        else:
            mot_score = 55

        factors.append(MatchFactor(
            name="motivator_match",
            category="motivation",
            score=mot_score,
            weight=0.3,
            signal_strength="moderate" if motivators else "weak",
            evidence=f"Motivators overlap: {motivators & growth_opps}" if (motivators and growth_opps) else "Limited motivator data",
        ))
        scores.append(mot_score)

        overall = sum(scores) / len(scores) if scores else 50
        return factors, overall

    def _score_environment(self, candidate: dict, job: dict, company: dict) -> tuple:
        """Score: Will they thrive in this environment?"""
        factors = []
        scores = []

        # Values alignment
        cand_values = set(v.lower() for v in candidate.get("values", []))
        company_values = set(v.lower() for v in company.get("values", []))
        if cand_values and company_values:
            val_overlap = len(cand_values & company_values) / max(1, len(company_values))
            val_score = min(100, 30 + val_overlap * 70)
        else:
            val_score = 55

        factors.append(MatchFactor(
            name="values_alignment",
            category="environment",
            score=val_score,
            weight=0.4,
            signal_strength="moderate",
            evidence=f"Shared values: {cand_values & company_values}" if (cand_values and company_values) else "Values data incomplete",
        ))
        scores.append(val_score)

        # Work style fit
        cand_style = candidate.get("work_style", "").lower()
        mgmt_style = job.get("management_style", "").lower()
        # Simple compatibility check
        style_score = 65  # Default moderate
        if cand_style and mgmt_style:
            if cand_style == mgmt_style:
                style_score = 90
            # Add more nuanced matching as needed

        factors.append(MatchFactor(
            name="work_style_fit",
            category="environment",
            score=style_score,
            weight=0.3,
            signal_strength="inferred",
            evidence=f"Candidate: {cand_style}, Manager: {mgmt_style}" if (cand_style and mgmt_style) else "Style data limited",
        ))
        scores.append(style_score)

        # Company reputation factor
        rep_score_raw = company.get("reputation_score", 70)
        rep_score = min(100, rep_score_raw)
        factors.append(MatchFactor(
            name="employer_reputation",
            category="environment",
            score=rep_score,
            weight=0.3,
            signal_strength="strong" if company.get("reputation_score") else "inferred",
            evidence=f"Company reputation: {rep_score_raw:.0f}/100",
        ))
        scores.append(rep_score)

        overall = sum(scores) / len(scores) if scores else 50
        return factors, overall

    def _score_trajectory(self, candidate: dict, job: dict) -> tuple:
        """Score: Will they grow with us?"""
        factors = []
        scores = []

        # Growth areas alignment with job opportunities
        growth_areas = set(g.lower() for g in candidate.get("growth_areas", []))
        growth_opps = set(g.lower() for g in job.get("growth_opportunities", []))

        if growth_areas and growth_opps:
            growth_match = len(growth_areas & growth_opps) / max(1, len(growth_areas))
            growth_score = min(100, 30 + growth_match * 70)
            evidence = f"Growth alignment: {growth_areas & growth_opps}"
        else:
            growth_score = 55
            evidence = "Growth data limited"

        factors.append(MatchFactor(
            name="growth_alignment",
            category="trajectory",
            score=growth_score,
            weight=0.5,
            signal_strength="moderate" if growth_areas else "weak",
            evidence=evidence,
        ))
        scores.append(growth_score)

        # Learning velocity (inferred from career moves)
        career_moves = candidate.get("career_moves", [])
        if len(career_moves) >= 2:
            # Check for upward movement
            velocity_score = min(100, 40 + len(career_moves) * 15)
        else:
            velocity_score = 50

        factors.append(MatchFactor(
            name="learning_velocity",
            category="trajectory",
            score=velocity_score,
            weight=0.5,
            signal_strength="moderate" if career_moves else "weak",
            evidence=f"{len(career_moves)} career transitions analyzed",
        ))
        scores.append(velocity_score)

        overall = sum(scores) / len(scores) if scores else 50
        return factors, overall

    def _find_brilliance(self, factors: list, quadrant_scores: dict) -> list:
        """Identify signs this person will 'actualize their brilliance' (Jared's philosophy)."""
        brilliance = []

        # All quadrants above 70 = rare holistic match
        if all(s >= 70 for s in quadrant_scores.values()):
            brilliance.append("Balanced excellence — strong across all four quadrants")

        # Any factor above 90 = standout strength
        for f in factors:
            if f.score >= 90:
                brilliance.append(f"Exceptional {f.name}: {f.evidence}")

        # Trajectory + Motivation both high = growth-oriented person in growth-oriented role
        if quadrant_scores.get("trajectory", 0) >= 80 and quadrant_scores.get("motivation", 0) >= 80:
            brilliance.append("High growth candidate with strong motivation — brilliance actualization likely")

        return brilliance[:5]

    def _assess_mutual_fit(self, candidate: dict, job: dict, company: dict, scores: dict) -> list:
        """Why does THIS match benefit BOTH sides?"""
        notes = []

        if scores.get("capability", 0) >= 70 and scores.get("trajectory", 0) >= 70:
            notes.append("Company gets proven skills + growth mindset. Candidate gets room to evolve.")

        if scores.get("environment", 0) >= 75:
            notes.append("Cultural alignment suggests long tenure — retention benefit for employer, belonging for candidate.")

        if scores.get("motivation", 0) >= 80:
            notes.append("Candidate is genuinely drawn to this role — intrinsic motivation drives performance.")

        if not notes:
            notes.append("Match is functional but may lack deeper mutual benefit — probe in interview.")

        return notes

    def _get_verdict(self, score: float) -> str:
        for threshold, verdict in self.VERDICT_MAP:
            if score >= threshold:
                return verdict
        return "Not This Role"
