"""
Origination Tracking — Candidate Source Attribution Engine
Meridian HR Intelligence — Pure Technology

Tracks where candidates come from, measures source effectiveness,
and optimizes recruitment spend allocation.

Attribution Model:
- First-touch: Which source first brought the candidate in
- Last-touch: Which source led to the application
- Multi-touch: Weighted credit across all touchpoints
- Influenced: Sources that touched the candidate at any point
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import json
import os


@dataclass
class Touchpoint:
    """A single candidate interaction with a recruitment source."""
    source: str  # "linkedin_organic", "indeed_paid", "referral", "career_page", etc.
    channel: str  # "paid", "organic", "referral", "direct", "event"
    timestamp: str
    action: str  # "viewed_posting", "clicked_ad", "referred_by", "applied", "attended_event"
    metadata: dict  # Source-specific data (campaign_id, referrer_name, etc.)


@dataclass
class SourceAttribution:
    """Attribution result for a single source."""
    source: str
    channel: str
    first_touch_credit: float  # 0-1
    last_touch_credit: float  # 0-1
    multi_touch_credit: float  # 0-1
    influenced: bool
    touchpoint_count: int


@dataclass
class CandidateOrigination:
    """Complete origination record for a candidate."""
    candidate_id: str
    candidate_name: str
    job_id: str
    first_touch_source: str
    last_touch_source: str
    touchpoints: list
    attributions: list
    total_touchpoints: int
    days_from_first_touch_to_apply: int
    primary_channel: str

    def to_dict(self):
        return {
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "job_id": self.job_id,
            "first_touch_source": self.first_touch_source,
            "last_touch_source": self.last_touch_source,
            "total_touchpoints": self.total_touchpoints,
            "days_to_apply": self.days_from_first_touch_to_apply,
            "primary_channel": self.primary_channel,
            "attributions": [
                {
                    "source": a.source,
                    "channel": a.channel,
                    "first_touch_credit": round(a.first_touch_credit, 2),
                    "last_touch_credit": round(a.last_touch_credit, 2),
                    "multi_touch_credit": round(a.multi_touch_credit, 2),
                    "influenced": a.influenced,
                }
                for a in self.attributions
            ],
        }


@dataclass
class SourceEffectiveness:
    """Aggregate effectiveness metrics for a recruitment source."""
    source: str
    channel: str
    total_candidates: int
    total_hires: int
    conversion_rate: float  # candidates → hires
    avg_quality_score: float  # average SMART SEARCH score of candidates from this source
    avg_time_to_hire_days: float
    cost_per_candidate: float
    cost_per_hire: float
    roi_score: float  # composite effectiveness score 0-100

    def to_dict(self):
        return {
            "source": self.source,
            "channel": self.channel,
            "total_candidates": self.total_candidates,
            "total_hires": self.total_hires,
            "conversion_rate": round(self.conversion_rate, 3),
            "avg_quality_score": round(self.avg_quality_score, 1),
            "avg_time_to_hire_days": round(self.avg_time_to_hire_days, 1),
            "cost_per_candidate": round(self.cost_per_candidate, 2),
            "cost_per_hire": round(self.cost_per_hire, 2),
            "roi_score": round(self.roi_score, 1),
        }


class OriginationTracker:
    """
    Tracks and attributes candidate sources across the hiring pipeline.

    Supported Sources:
    - Job boards: Indeed, LinkedIn, Glassdoor, ZipRecruiter, Monster
    - Social: LinkedIn organic, Twitter/X, Instagram
    - Referral: Employee referrals (tracked by referrer)
    - Direct: Career page, company website
    - Events: Job fairs, campus recruiting, meetups
    - Agency: Staffing agencies, recruiters
    - Paid: Sponsored listings, PPC campaigns, display ads
    """

    KNOWN_SOURCES = {
        "indeed_paid": "paid",
        "indeed_organic": "organic",
        "linkedin_paid": "paid",
        "linkedin_organic": "organic",
        "linkedin_recruiter": "paid",
        "glassdoor": "organic",
        "ziprecruiter": "paid",
        "career_page": "direct",
        "company_website": "direct",
        "employee_referral": "referral",
        "agency": "paid",
        "job_fair": "event",
        "campus_recruiting": "event",
        "social_media": "organic",
        "google_ads": "paid",
        "other": "organic",
    }

    def __init__(self, config_path: Optional[str] = None):
        config_file = config_path or os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(config_file):
            with open(config_file) as f:
                self.config = json.load(f)
        else:
            self.config = {}

    def attribute_candidate(
        self,
        candidate_id: str,
        candidate_name: str,
        job_id: str,
        touchpoints: list,
    ) -> CandidateOrigination:
        """
        Attribute a candidate's origination across all touchpoints.

        Args:
            touchpoints: List of Touchpoint objects in chronological order
        """
        if not touchpoints:
            return CandidateOrigination(
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                job_id=job_id,
                first_touch_source="unknown",
                last_touch_source="unknown",
                touchpoints=[],
                attributions=[],
                total_touchpoints=0,
                days_from_first_touch_to_apply=0,
                primary_channel="unknown",
            )

        # Sort by timestamp
        sorted_tp = sorted(touchpoints, key=lambda t: t.timestamp)
        first = sorted_tp[0]
        last = sorted_tp[-1]

        # Calculate days from first touch to application
        try:
            first_dt = datetime.fromisoformat(first.timestamp)
            last_dt = datetime.fromisoformat(last.timestamp)
            days_to_apply = (last_dt - first_dt).days
        except (ValueError, TypeError):
            days_to_apply = 0

        # Build attributions
        unique_sources = {}
        for tp in sorted_tp:
            if tp.source not in unique_sources:
                unique_sources[tp.source] = {
                    "channel": tp.channel or self.KNOWN_SOURCES.get(tp.source, "organic"),
                    "count": 0,
                    "is_first": tp == first,
                    "is_last": tp == last,
                }
            unique_sources[tp.source]["count"] += 1

        n_sources = len(unique_sources)
        attributions = []
        for source, info in unique_sources.items():
            # Multi-touch: equal credit across all sources, with bonuses for first/last
            base_credit = 1.0 / n_sources if n_sources > 0 else 0
            multi_credit = base_credit
            if info["is_first"]:
                multi_credit += 0.1
            if info["is_last"]:
                multi_credit += 0.1
            # Normalize
            multi_credit = min(1.0, multi_credit)

            attributions.append(SourceAttribution(
                source=source,
                channel=info["channel"],
                first_touch_credit=1.0 if info["is_first"] else 0.0,
                last_touch_credit=1.0 if info["is_last"] else 0.0,
                multi_touch_credit=round(multi_credit, 3),
                influenced=True,
                touchpoint_count=info["count"],
            ))

        # Determine primary channel
        channel_counts = {}
        for tp in sorted_tp:
            ch = tp.channel or self.KNOWN_SOURCES.get(tp.source, "organic")
            channel_counts[ch] = channel_counts.get(ch, 0) + 1
        primary_channel = max(channel_counts, key=channel_counts.get) if channel_counts else "unknown"

        return CandidateOrigination(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            job_id=job_id,
            first_touch_source=first.source,
            last_touch_source=last.source,
            touchpoints=sorted_tp,
            attributions=attributions,
            total_touchpoints=len(sorted_tp),
            days_from_first_touch_to_apply=days_to_apply,
            primary_channel=primary_channel,
        )

    def calculate_source_effectiveness(
        self,
        source: str,
        candidates: list,
        hires: list,
        total_spend: float,
        avg_quality_scores: Optional[list] = None,
        avg_time_to_hire: Optional[float] = None,
    ) -> SourceEffectiveness:
        """
        Calculate effectiveness metrics for a recruitment source.

        Args:
            source: Source identifier
            candidates: List of candidate IDs from this source
            hires: List of candidate IDs hired from this source
            total_spend: Total $ spent on this source
            avg_quality_scores: SMART SEARCH scores for candidates from this source
            avg_time_to_hire: Average days to hire from this source
        """
        n_candidates = len(candidates)
        n_hires = len(hires)
        conversion = n_hires / n_candidates if n_candidates > 0 else 0
        cost_per_candidate = total_spend / n_candidates if n_candidates > 0 else 0
        cost_per_hire = total_spend / n_hires if n_hires > 0 else float("inf")

        avg_quality = (
            sum(avg_quality_scores) / len(avg_quality_scores) if avg_quality_scores else 0
        )

        # ROI composite score (weighted)
        # Higher conversion, higher quality, lower cost, faster hire = better
        roi_factors = []
        roi_factors.append(min(100, conversion * 500))  # 20% conversion = 100
        roi_factors.append(avg_quality)  # Already 0-100
        if cost_per_hire < float("inf"):
            roi_factors.append(max(0, 100 - cost_per_hire / 100))  # Lower cost = higher score
        if avg_time_to_hire:
            roi_factors.append(max(0, 100 - avg_time_to_hire * 2))  # Faster = higher score

        roi = sum(roi_factors) / len(roi_factors) if roi_factors else 0

        return SourceEffectiveness(
            source=source,
            channel=self.KNOWN_SOURCES.get(source, "organic"),
            total_candidates=n_candidates,
            total_hires=n_hires,
            conversion_rate=conversion,
            avg_quality_score=avg_quality,
            avg_time_to_hire_days=avg_time_to_hire or 0,
            cost_per_candidate=cost_per_candidate,
            cost_per_hire=cost_per_hire if cost_per_hire < float("inf") else 0,
            roi_score=roi,
        )

    def recommend_budget_allocation(
        self,
        source_metrics: list,
        total_budget: float,
        target_hires: int,
    ) -> dict:
        """
        Recommend how to allocate recruitment budget across sources.

        Uses ROI scores to proportionally allocate budget,
        with minimum floor for diversification.
        """
        if not source_metrics:
            return {"error": "No source metrics provided"}

        # Sort by ROI
        sorted_sources = sorted(source_metrics, key=lambda s: s.roi_score, reverse=True)

        # Calculate proportional allocation based on ROI
        total_roi = sum(s.roi_score for s in sorted_sources)
        if total_roi == 0:
            # Equal distribution if no ROI data
            per_source = total_budget / len(sorted_sources)
            return {
                "allocations": {s.source: round(per_source, 2) for s in sorted_sources},
                "strategy": "Equal distribution — insufficient ROI data for optimization",
            }

        min_allocation = total_budget * 0.05  # 5% floor per source for diversification
        remaining = total_budget - (min_allocation * len(sorted_sources))

        allocations = {}
        for s in sorted_sources:
            roi_share = (s.roi_score / total_roi) * remaining
            allocations[s.source] = round(min_allocation + roi_share, 2)

        # Expected hires per source
        expected_hires = {}
        for s in sorted_sources:
            if s.cost_per_hire > 0:
                expected_hires[s.source] = round(allocations[s.source] / s.cost_per_hire, 1)
            else:
                expected_hires[s.source] = 0

        total_expected = sum(expected_hires.values())

        return {
            "total_budget": total_budget,
            "target_hires": target_hires,
            "allocations": allocations,
            "expected_hires_per_source": expected_hires,
            "total_expected_hires": total_expected,
            "gap": max(0, target_hires - total_expected),
            "top_recommendation": f"Increase investment in {sorted_sources[0].source} (ROI: {sorted_sources[0].roi_score:.0f}/100)" if sorted_sources else "N/A",
            "cut_recommendation": f"Reduce spend on {sorted_sources[-1].source} (ROI: {sorted_sources[-1].roi_score:.0f}/100)" if len(sorted_sources) > 1 else "N/A",
        }
