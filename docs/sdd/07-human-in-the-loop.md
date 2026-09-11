# Human-in-the-Loop

## CURRENT STATE
- **IMPLEMENTED**: `applications` table has a `human_approved` boolean flag.
- **PARTIAL**: The Next.js dashboard exists, allowing users to view generated CVs and jobs, but the workflow for "Edit -> Approve -> Reject" might lack robust endpoints for granular document editing.

## TARGET DIRECTION
AgentHire is a copilot, not a fully autonomous bot.
- **Review Gate**: Applications require explicit human approval before submission.
- **Editing**: Humans can edit the personalized CV and cover letter directly in the dashboard before approval.
- **Feedback Loop**: Human edits should ideally feedback into the Candidate Knowledge Base if new skills or better phrasings are introduced.
