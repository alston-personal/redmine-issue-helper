import os
import yaml
import logging

logger = logging.getLogger("RedmineHelper.Generator")

class TemplateEngine:
    def __init__(self, template_dir):
        self.template_dir = template_dir

    def load_template(self, name):
        path = os.path.join(self.template_dir, f"{name}.yaml")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Template {name} not found in {self.template_dir}")
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

class IssueGenerator:
    def __init__(self, template_engine):
        self.template_engine = template_engine

    def translate_title(self, chinese_title):
        # Mock translation logic: In reality, could call LLM here
        # For now, we return a draft marker if we can't translate
        logger.info(f"Translating title: {chinese_title}")
        return f"[Draft] {chinese_title}"

    def generate_description(self, template_name, fields_data):
        template = self.template_engine.load_template(template_name)
        fmt = template.get('description_format', "")
        
        # Fill missing fields with placeholders
        all_fields = template.get('required_fields', []) + template.get('optional_fields', [])
        data = {f: fields_data.get(f, "N/A") for f in all_fields}
        
        return fmt.format(**data)

    def interactive_collect(self, template_name, initial_title):
        template = self.template_engine.load_template(template_name)
        questions = template.get('questions', {})
        collected_data = {}
        
        print(f"\n--- Creating Issue: {initial_title} ---")
        print(f"Template: {template['name']} ({template['description']})\n")
        
        for field, question in questions.items():
            value = input(f"[?] {question} ")
            collected_data[field] = value if value.strip() else "n/a"
            
        english_title = self.translate_title(initial_title)
        description = self.generate_description(template_name, collected_data)
        
        return english_title, description, collected_data
