from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import sys

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import ConfigManager
from src.core.issue import Issue, IssueStore
from src.core.redmine import RedmineClient
from src.generator.engine import TemplateEngine, IssueGenerator

app = FastAPI(title="Redmine Issue Helper API")

# Mount Static Files
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = ConfigManager()
issue_store = IssueStore(config.pending_dir, config.uploaded_dir)
template_engine = TemplateEngine(config.template_dir)
generator = IssueGenerator(template_engine)

class IssueCreateRequest(BaseModel):
    title: str
    template: str
    fields: Dict[str, str]

@app.get("/templates")
async def get_templates():
    templates = []
    for filename in os.listdir(config.template_dir):
        if filename.endswith(".yaml"):
            name = filename[:-5]
            tpl = template_engine.load_template(name)
            templates.append(tpl)
    return templates

@app.get("/issues/pending")
async def list_pending():
    issues = issue_store.get_pending_issues()
    return [issue.data for path, issue in issues]

@app.get("/issues/uploaded")
async def list_uploaded():
    # Helper to list uploaded issues (need custom logic in IssueStore)
    import glob
    files = glob.glob(os.path.join(config.uploaded_dir, "*.yaml"))
    results = []
    for f in files:
        results.append(Issue.load(f).data)
    results.sort(key=lambda x: x['system']['created_at'], reverse=True)
    return results

@app.get("/issues/{issue_id}")
async def get_issue(issue_id: str):
    pending = issue_store.get_pending_issues()
    for path, issue in pending:
        if issue.data['system']['id'] == issue_id:
            return issue.data
    raise HTTPException(status_code=404, detail="Issue not found")

@app.put("/issues/{issue_id}")
async def update_issue(issue_id: str, data: Dict):
    pending = issue_store.get_pending_issues()
    for path, issue in pending:
        if issue.data['system']['id'] == issue_id:
            issue.data.update(data)
            # Ensure system ID and created_at don't change
            issue.data['system']['id'] = issue_id 
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(issue.data, f, allow_unicode=True, sort_keys=False)
            return {"status": "success", "issue": issue.data}
    raise HTTPException(status_code=404, detail="Issue not found")

@app.delete("/issues/{issue_id}")
async def delete_issue(issue_id: str):
    pending = issue_store.get_pending_issues()
    for path, issue in pending:
        if issue.data['system']['id'] == issue_id:
            os.remove(path)
            return {"status": "success"}
    raise HTTPException(status_code=404, detail="Issue not found")

@app.post("/issues/generate")
async def generate_preview(req: IssueCreateRequest):
    try:
        # Pass title to help generator infer content
        eng_title = generator.translate_title(req.title)
        description = generator.generate_description(req.template, req.fields, title_context=req.title)
        
        return {
            "english_title": eng_title,
            "description": description
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/issues/draft")
async def create_draft(req: IssueCreateRequest):
    try:
        eng_title = generator.translate_title(req.title)
        description = generator.generate_description(req.template, req.fields, title_context=req.title)
        
        issue = Issue.create_new(
            original_title=req.title,
            english_title=eng_title,
            description=description,
            template_name=req.template,
            redmine_fields={
                "project_id": config.project_identifier,
                "tracker_id": config.get('redmine.default_tracker'),
                "priority_id": config.get('field_mapping.priority_id'),
                "status_id": config.get('field_mapping.status_id')
            }
        )
        # Add the raw fields to the issue data for easier editing later
        issue.data['content']['form_data'] = req.fields
        
        path = issue.save(config.pending_dir)
        return {"status": "success", "path": path, "issue": issue.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/issues/upload/{issue_id}")
async def upload_issue(issue_id: str):
    pending = issue_store.get_pending_issues()
    target_path = None
    target_issue = None
    
    for path, issue in pending:
        if issue.data['system']['id'] == issue_id:
            target_path = path
            target_issue = issue
            break
            
    if not target_issue:
        raise HTTPException(status_code=404, detail="Issue not found in pending")
        
    client = RedmineClient(config.redmine_base_url, config.api_key)
    try:
        rf = target_issue.data.get('redmine_fields', {})
        # Extract known ones for positional args, pass the rest as kwargs
        known_keys = ['project_id', 'tracker_id', 'priority_id', 'status_id']
        other_fields = {k: v for k, v in rf.items() if k not in known_keys}
        
        rid, rurl = client.create_issue(
            project_id=rf.get('project_id'),
            subject=target_issue.data['content']['english_title'],
            description=target_issue.data['content']['description'],
            tracker_id=rf.get('tracker_id'),
            priority_id=rf.get('priority_id'),
            status_id=rf.get('status_id'),
            **other_fields
        )
        issue_store.move_to_uploaded(target_path, rid, rurl)
        return {"status": "success", "redmine_id": rid, "url": rurl}
    except Exception as e:
        issue_store.mark_failed(target_path, str(e))
        return {"status": "failed", "error": str(e)}

@app.get("/config")
async def get_config():
    return {
        "redmine_url": config.redmine_base_url,
        "project": config.project_identifier,
        "pending_dir": config.pending_dir
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
