import click
import os
import sys
from src.core.config import ConfigManager
from src.core.issue import Issue, IssueStore
from src.core.redmine import RedmineClient
from src.generator.engine import TemplateEngine, IssueGenerator
from src.utils.logger import setup_logger

# Add src to path just in case
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

logger = setup_logger()

try:
    config = ConfigManager()
except Exception as e:
    print(f"Error loading configuration: {e}")
    sys.exit(1)

issue_store = IssueStore(config.pending_dir, config.uploaded_dir)
template_engine = TemplateEngine(config.template_dir)
generator = IssueGenerator(template_engine)

@click.group()
def cli():
    """Redmine Issue Helper CLI"""
    pass

@cli.command()
@click.option('--title', prompt='Issue Chinese Title', help='The Chinese title of the issue')
@click.option('--template', default=config.get('settings.default_template', 'bug_report'), help='Template to use')
def create(title, template):
    """Create a new issue draft YAML file."""
    try:
        eng_title, description, raw_data = generator.interactive_collect(template, title)
        
        # User review
        print("\n--- Draft Generated ---")
        print(f"Title: {eng_title}")
        print(f"Description:\n{description}")
        
        if click.confirm('Do you want to save this draft?', default=True):
            issue = Issue.create_new(
                original_title=title,
                english_title=eng_title,
                description=description,
                template_name=template,
                redmine_fields={
                    "project_id": config.project_identifier,
                    "tracker_id": config.get('redmine.default_tracker'), # Should ideally map names to IDs or use names if API supports
                    "priority_id": config.get('field_mapping.priority_id'),
                    "status_id": config.get('field_mapping.status_id')
                }
            )
            saved_path = issue.save(config.pending_dir)
            logger.info(f"Issue saved to {saved_path}")
            print(f"Success! Saved to {saved_path}")
        else:
            print("Cancelled.")
    except Exception as e:
        logger.error(f"Error in create command: {e}")
        print(f"Error: {e}")

@cli.command()
def upload():
    """Upload pending issues to Redmine."""
    pending = issue_store.get_pending_issues()
    if not pending:
        print("No pending issues found.")
        return

    client = RedmineClient(config.redmine_base_url, config.api_key)
    
    print(f"Found {len(pending)} issues to upload.\n")
    
    for path, issue in pending:
        title = issue.data['content']['english_title']
        print(f"Uploading: {title} ...")
        
        try:
            # Prepare data
            rf = issue.data.get('redmine_fields', {})
            issue_id, issue_url = client.create_issue(
                project_id=rf.get('project_id'),
                subject=title,
                description=issue.data['content']['description'],
                tracker_id=rf.get('tracker_id'),
                priority_id=rf.get('priority_id'),
                status_id=rf.get('status_id')
            )
            
            # Update local state
            new_path = issue_store.move_to_uploaded(path, issue_id, issue_url)
            logger.info(f"Successfully uploaded issue {issue_id}. Moved to {new_path}")
            print(f"  -> SUCCESS! Created Redmine Issue #{issue_id}")
            print(f"  -> Link: {issue_url}")
            
        except Exception as e:
            issue_store.mark_failed(path, e)
            logger.error(f"Failed to upload {path}: {e}")
            print(f"  -> FAILED: {e}")

@cli.command()
def list():
    """List all pending issues."""
    pending = issue_store.get_pending_issues()
    if not pending:
        print("No pending issues.")
        return
    
    print(f"{'Created At':<25} | {'Title':<40} | {'Attempts':<8}")
    print("-" * 78)
    for path, issue in pending:
        sys_data = issue.data['system']
        title = issue.data['content']['original_title']
        print(f"{sys_data['created_at']:<25} | {title[:38]:<40} | {sys_data['upload_attempts']:<8}")

if __name__ == '__main__':
    cli()
