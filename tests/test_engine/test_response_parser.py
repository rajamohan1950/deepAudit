import json
import pytest

from app.engine.llm.response_parser import ResponseParser


@pytest.fixture
def parser():
    return ResponseParser()


def test_parse_valid_json(parser):
    response = json.dumps({
        "signals": [
            {
                "signal_text": "SQL injection in user search endpoint via unparameterized query",
                "severity": "P0",
                "score": 9.5,
                "score_type": "cvss",
                "evidence": "app/api/users.py:L45 — f-string SQL query",
                "failure_scenario": "Attacker sends crafted search term to extract all user data",
                "remediation": "Use parameterized queries via SQLAlchemy ORM instead of raw f-strings",
                "effort": "S",
                "confidence": 0.95,
                "references": ["OWASP-A03"],
            }
        ]
    })

    signals = parser.parse(response, category_id=3)
    assert len(signals) == 1
    assert signals[0].severity == "P0"
    assert signals[0].score == 9.5


def test_reject_vague_signal(parser):
    response = json.dumps({
        "signals": [
            {
                "signal_text": "Bad auth",
                "severity": "P2",
                "score": 5.0,
                "score_type": "risk",
                "evidence": "",
                "failure_scenario": "",
                "remediation": "Improve it",
                "effort": "M",
            }
        ]
    })

    signals = parser.parse(response, category_id=1)
    assert len(signals) == 0


def test_parse_json_in_markdown(parser):
    response = '''Here are the findings:

```json
{
  "signals": [
    {
      "signal_text": "Missing rate limiting on login endpoint allows brute force attacks",
      "severity": "P1",
      "score": 7.5,
      "score_type": "cvss",
      "evidence": "app/auth/routes.py:L12 — no rate limit decorator",
      "failure_scenario": "Attacker runs 10K login attempts per minute to guess passwords",
      "remediation": "Add rate limiting decorator: @limiter.limit('5/minute') on POST /login",
      "effort": "S",
      "confidence": 0.9
    }
  ]
}
```'''

    signals = parser.parse(response, category_id=1)
    assert len(signals) == 1
    assert signals[0].severity == "P1"
