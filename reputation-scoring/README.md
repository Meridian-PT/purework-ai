# Company Reputation Scoring Model

Scores a company's employer reputation on a 0-100 scale across 6 dimensions.
Used by Bounty Hunter to help candidates evaluate potential employers and by
recruiters to benchmark client companies.

## Dimensions

| Dimension | Weight | Sources |
|-----------|--------|---------|
| Glassdoor Rating | 20% | Glassdoor API |
| Employee Retention | 20% | Company-reported or LinkedIn data |
| Culture Indicators | 15% | Job postings language analysis, benefits offered |
| Growth Trajectory | 15% | Hiring velocity, revenue signals |
| Compensation Competitiveness | 15% | Comp benchmarks vs market |
| DEI & Values Alignment | 15% | Public commitments, leadership diversity |

## Scoring

- **90-100**: Exceptional employer — top 10%
- **75-89**: Strong employer — above average
- **60-74**: Average employer — meets baseline
- **40-59**: Below average — yellow flags
- **0-39**: Poor reputation — red flags for candidates

## Usage

```python
from reputation_scoring.model import ReputationScorer

scorer = ReputationScorer()
score = scorer.score_company({
    "glassdoor_rating": 4.2,
    "retention_rate": 0.85,
    "benefits_score": 7,
    "hiring_velocity": 0.15,
    "comp_percentile": 65,
    "dei_score": 6
})
print(score)  # CompanyReputation(overall=78, grade="Strong", ...)
```
