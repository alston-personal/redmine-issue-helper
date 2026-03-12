import os
import yaml
from dotenv import load_dotenv

load_dotenv()

class ConfigManager:
    def __init__(self, config_path="config/app.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.api_key = os.getenv("REDMINE_API_KEY")
        if not self.api_key:
            raise ValueError("REDMINE_API_KEY not found in .env file")

    def get(self, key, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    @property
    def redmine_base_url(self):
        return self.get('redmine.base_url')

    @property
    def project_identifier(self):
        return self.get('redmine.project_identifier')

    @property
    def pending_dir(self):
        return self.get('paths.pending_dir', './issues/pending')

    @property
    def uploaded_dir(self):
        return self.get('paths.uploaded_dir', './issues/uploaded')

    @property
    def template_dir(self):
        return self.get('paths.template_dir', './config/templates')
