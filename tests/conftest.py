import pytest

@pytest.fixture
def sample_job_data():
    return {
        "portal": "linkedin",
        "title": "Software Engineer",
        "company": "Tech Corp",
        "url": "https://linkedin.com/jobs/123"
    }
