from agents.core.models import Job, JobStatus, PortalName
from datetime import datetime, timezone
import json

def test_job_model_creation():
    job = Job(
        title="Software Engineer",
        company="Tech Corp",
        url="https://example.com/job",
        portal=PortalName.LINKEDIN
    )
    assert job.title == "Software Engineer"
    assert job.status == JobStatus.DISCOVERED
    assert job.modality is None
    assert job.id is not None

def test_job_serialization():
    job = Job(
        title="Backend Dev",
        company="API Inc",
        url="https://example.com/api",
        portal=PortalName.CHILETRABAJOS,
        salary_min=1000,
        salary_max=2000,
        posted_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        discovered_at=datetime(2023, 1, 2, tzinfo=timezone.utc)
    )
    d = job.to_dict()
    assert d["title"] == "Backend Dev"
    assert d["company"] == "API Inc"
    assert d["portal"] == "chiletrabajos"
    assert d["salary_min"] == 1000
    assert d["posted_at"] == "2023-01-01T00:00:00+00:00"
    assert d["discovered_at"] == "2023-01-02T00:00:00+00:00"
    
    # Verify it can be JSON serialized
    json.dumps(d)

def test_job_status_transition(sample_job_data):
    job = Job(**sample_job_data)
    assert job.status == JobStatus.DISCOVERED
    job.status = JobStatus.APPLIED
    assert job.status == JobStatus.APPLIED
