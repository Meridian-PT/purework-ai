"""
Company Reputation Scoring Model
Meridian HR Intelligence — Pure Technology

Scores employer reputation on a 0-100 scale across 6 weighted dimensions.
"""

from dataclasses import dataclass, field
from typing import Optional
import json
import os


@dataclass
class DimensionScore:
    """Score for a single reputation dimension."""
    name: str
    raw_value: float
    normalized_score: float  # 0-100
    weight: float
    weighted_score: float
    data_quality: str  # "verified", "estimated", "missing"


@dataclass
class CompanyReputation:
    """Complete reputation assessment for a company."""
    company_name: str
    overall_score: float
    grade: str
    dimensions: list
    confidence: float  # 0-1, based on data quality
    flags: list
    recommendations: list

    def to_dict(self):
        return {
            "company_name": self.company_name,
            "overall_score": round(self.overall_score, 1),
            "grade": self.grade,
            "confidence": round(self.confidence, 2),
            "dimensions": [
                {
                    "name": d.name,
                    "raw_value": d.raw_value,
                    "normalized_score": round(d.normalized_score, 1),
                    "weight": d.weight,
                    "weighted_score": round(d.weighted_score, 1),
                    "data_quality": d.data_quality,
                }
                for d in self.dimensions
            ],
            "flags": self.flags,
            "recommendations": self.recommendations,
        }


class ReputationScorer:
    """
    Scores a company's employer reputation across 6 dimensions.

    Each dimension is normalized to 0-100, weighted, and combined
    into an overall reputation score.
    """

    # Default weights — configurable via config.json
    DEFAULT_WEIGHTS = {
        "glassdoor_rating": 0.20,
        "retention_rate": 0.20,
        "culture_indicators": 0.15,
        "growth_trajectory": 0.15,
        "comp_competitiveness": 0.15,
        "dei_alignment": 0.15,
    }

    GRADE_THRESHOLDS = [
        (90, "Exceptional"),
        (75, "Strong"),
        (60, "Average"),
        (40, "Below Average"),
        (0, "Poor"),
    ]

    def __init__(self, config_path: Optional[str] = None):
        self.weights = self.DEFAULT_WEIGHTS.copy()
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
                self.weights.update(config.get("weights", {}))

    def score_company(self, company_name: str, data: dict) -> CompanyReputation:
        """
        Score a company's reputation.

        Args:
            company_name: Name of the company
            data: Dict with keys matching dimension names. Values:
                - glassdoor_rating: 0-5 scale
                - retention_rate: 0-1 (percentage as decimal)
                - culture_indicators: 0-10 composite score
                - growth_trajectory: -1 to 1 (negative = shrinking)
                - comp_competitiveness: 0-100 percentile
                - dei_alignment: 0-10 composite score

        Returns:
            CompanyReputation with overall score, grade, and breakdown
        """
        dimensions = []
        flags = []
        data_quality_scores = []

        # Score each dimension
        for dim_name, weight in self.weights.items():
            raw_value = data.get(dim_name)

            if raw_value is None:
                # Missing data — apply penalty and flag
                dim = DimensionScore(
                    name=dim_name,
                    raw_value=0,
                    normalized_score=50,  # Assume average when missing
                    weight=weight,
                    weighted_score=50 * weight,
                    data_quality="missing",
                )
                flags.append(f"Missing data for {dim_name} — using average estimate")
                data_quality_scores.append(0.3)
            else:
                normalized = self._normalize(dim_name, raw_value)
                dim = DimensionScore(
                    name=dim_name,
                    raw_value=raw_value,
                    normalized_score=normalized,
                    weight=weight,
                    weighted_score=normalized * weight,
                    data_quality="verified",
                )
                data_quality_scores.append(1.0)

                # Flag concerning scores
                if normalized < 40:
                    flags.append(f"Red flag: {dim_name} scored {normalized:.0f}/100")
                elif normalized < 60:
                    flags.append(f"Yellow flag: {dim_name} below average at {normalized:.0f}/100")

            dimensions.append(dim)

        # Calculate overall
        overall = sum(d.weighted_score for d in dimensions)
        confidence = sum(data_quality_scores) / len(data_quality_scores) if data_quality_scores else 0
        grade = self._grade(overall)

        # Generate recommendations
        recommendations = self._generate_recommendations(dimensions, flags)

        return CompanyReputation(
            company_name=company_name,
            overall_score=overall,
            grade=grade,
            dimensions=dimensions,
            confidence=confidence,
            flags=flags,
            recommendations=recommendations,
        )

    def _normalize(self, dimension: str, value: float) -> float:
        """Normalize raw values to 0-100 scale."""
        normalizers = {
            "glassdoor_rating": lambda v: min(100, max(0, (v / 5.0) * 100)),
            "retention_rate": lambda v: min(100, max(0, v * 100)),
            "culture_indicators": lambda v: min(100, max(0, (v / 10.0) * 100)),
            "growth_trajectory": lambda v: min(100, max(0, (v + 1) / 2 * 100)),
            "comp_competitiveness": lambda v: min(100, max(0, v)),
            "dei_alignment": lambda v: min(100, max(0, (v / 10.0) * 100)),
        }
        normalizer = normalizers.get(dimension, lambda v: min(100, max(0, v)))
        return normalizer(value)

    def _grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        for threshold, grade in self.GRADE_THRESHOLDS:
            if score >= threshold:
                return grade
        return "Poor"

    def _generate_recommendations(self, dimensions: list, flags: list) -> list:
        """Generate actionable recommendations based on scores."""
        recs = []
        sorted_dims = sorted(dimensions, key=lambda d: d.normalized_score)

        # Recommend improving weakest dimensions
        for dim in sorted_dims[:2]:
            if dim.normalized_score < 70:
                recs.append(
                    f"Improve {dim.name}: currently at {dim.normalized_score:.0f}/100. "
                    f"This dimension carries {dim.weight*100:.0f}% weight."
                )

        # Flag data quality issues
        missing = [d for d in dimensions if d.data_quality == "missing"]
        if missing:
            recs.append(
                f"Collect data for {len(missing)} missing dimension(s) to improve confidence: "
                + ", ".join(d.name for d in missing)
            )

        if not recs:
            recs.append("Strong reputation across all dimensions. Maintain current trajectory.")

        return recs


# Convenience function
def score_company(company_name: str, data: dict, config_path: Optional[str] = None) -> CompanyReputation:
    """Quick-score a company without instantiating the scorer."""
    scorer = ReputationScorer(config_path=config_path)
    return scorer.score_company(company_name, data)
