import requests
import logging

logger = logging.getLogger("RedmineHelper.RedmineClient")

class RedmineClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "X-Redmine-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def create_issue(self, project_id, subject, description, tracker_id=None, status_id=None, priority_id=None, **kwargs):
        url = f"{self.base_url}/issues.json"
        
        issue_data = {
            "issue": {
                "project_id": project_id,
                "subject": subject,
                "description": description
            }
        }
        
        if tracker_id:
            issue_data["issue"]["tracker_id"] = tracker_id
        if status_id:
            issue_data["issue"]["status_id"] = status_id
        if priority_id:
            issue_data["issue"]["priority_id"] = priority_id
            
        # Add extra fields (category_id, assignee_id, etc.)
        for k, v in kwargs.items():
            if v is not None:
                issue_data["issue"][k] = v

        try:
            response = requests.post(url, headers=self.headers, json=issue_data, timeout=10)
            response.raise_for_status()
            result = response.json()
            issue_id = result["issue"]["id"]
            issue_url = f"{self.base_url}/issues/{issue_id}"
            return issue_id, issue_url
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create issue on Redmine: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise e
