import os
import yaml
import uuid
from datetime import datetime
import glob

class Issue:
    def __init__(self, data=None):
        self.data = data or {}

    @classmethod
    def create_new(cls, original_title, english_title, description, template_name, redmine_fields=None):
        now = datetime.utcnow().isoformat() + "Z"
        system_id = str(uuid.uuid4())[:8]
        
        data = {
            "system": {
                "id": system_id,
                "created_at": now,
                "status": "pending",
                "template_name": template_name,
                "upload_attempts": 0,
                "upload_error": None,
                "redmine_issue_id": None,
                "redmine_issue_url": None
            },
            "content": {
                "original_title": original_title,
                "english_title": english_title,
                "description": description
            },
            "redmine_fields": redmine_fields or {}
        }
        return cls(data)

    def save(self, directory):
        filename = f"{self.data['system']['created_at'].replace(':', '-').split('.')[0]}_{self.data['system']['id']}.yaml"
        path = os.path.join(directory, filename)
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.data, f, allow_unicode=True, sort_keys=False)
        return path

    @classmethod
    def load(cls, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(data)

class IssueStore:
    def __init__(self, pending_dir, uploaded_dir):
        self.pending_dir = pending_dir
        self.uploaded_dir = uploaded_dir
        for d in [pending_dir, uploaded_dir]:
            if not os.path.exists(d):
                os.makedirs(d)

    def get_pending_issues(self):
        files = glob.glob(os.path.join(self.pending_dir, "*.yaml"))
        issues = []
        for f in files:
            issues.append((f, Issue.load(f)))
        
        # Sort by created_at
        issues.sort(key=lambda x: x[1].data['system']['created_at'])
        return issues

    def move_to_uploaded(self, file_path, issue_id, issue_url):
        issue = Issue.load(file_path)
        issue.data['system']['status'] = 'uploaded'
        issue.data['system']['redmine_issue_id'] = issue_id
        issue.data['system']['redmine_issue_url'] = issue_url
        
        filename = os.path.basename(file_path)
        new_path = os.path.join(self.uploaded_dir, filename)
        
        with open(new_path, 'w', encoding='utf-8') as f:
            yaml.dump(issue.data, f, allow_unicode=True, sort_keys=False)
        
        os.remove(file_path)
        return new_path

    def mark_failed(self, file_path, error_msg):
        issue = Issue.load(file_path)
        issue.data['system']['upload_attempts'] += 1
        issue.data['system']['upload_error'] = str(error_msg)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(issue.data, f, allow_unicode=True, sort_keys=False)
