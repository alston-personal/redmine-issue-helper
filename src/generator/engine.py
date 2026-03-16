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

    def generate_description(self, template_name, fields_data, title_context=""):
        template = self.template_engine.load_template(template_name)
        fmt = template.get('description_format', "")
        
        # Heuristic approach: if field is empty, try to provide a 'placeholder' or 'guessed' value
        all_fields = template.get('required_fields', []) + template.get('optional_fields', [])
        data = {}
        for f in all_fields:
            val = fields_data.get(f, "").strip()
            if not val:
                # Smarter inference from title
                if f == 'actual_result' and title_context:
                    if "不" in title_context or "錯" in title_context or "失敗" in title_context:
                        val = f"The system is currently: {title_context}"
                    else:
                        val = f"Issue observed: {title_context}"
                elif f == 'expected_result' and title_context:
                    val = "The system should function correctly without errors."
                elif f == 'steps':
                    val = "1. Navigate to the relevant page.\n2. Perform the action mentioned in the title.\n3. Observe the issue."
                elif f == 'frequency':
                    val = "Always"
                else:
                    val = f"[{f.replace('_', ' ').capitalize()}]"
            data[f] = val
        
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
