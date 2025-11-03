from agents.core.models import Job, JobStatus, PortalName

def test_job_creation(sample_job_data):
    job = Job(**sample_job_data)
    assert job.portal == PortalName.LINKEDIN
    assert job.title == "Software Engineer"
    assert job.status == JobStatus.DISCOVERED
    assert job.remote is False
    
def test_job_status_transition(sample_job_data):
    job = Job(**sample_job_data)
    assert job.status == JobStatus.DISCOVERED
    job.status = JobStatus.APPLIED
    assert job.status == JobStatus.APPLIED
