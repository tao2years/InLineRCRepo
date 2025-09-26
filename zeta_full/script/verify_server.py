from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import shutil
from pathlib import Path
import glob
from typing import List, Optional
import argparse
import os.path

app = FastAPI()

# Global variables to store paths
FEEDBACK_DIR = None
TRAIN_DIR = None
TRASH_DIR = None

def get_next_train_number() -> int:
    """Get the next available number for training examples."""
    files = glob.glob(os.path.join(TRAIN_DIR, "*.md"))
    if not files:
        return 1
    numbers = [int(os.path.basename(f).replace(".md", "")) for f in files]
    return max(numbers) + 1

def get_feedback_files() -> List[str]:
    """Get list of feedback files."""
    return sorted(glob.glob(os.path.join(FEEDBACK_DIR, "*.md")))

@app.get("/api/files")
async def get_files():
    """Get list of feedback files."""
    files = get_feedback_files()
    return {"files": [os.path.basename(f) for f in files]}

@app.get("/api/file/{filename}")
async def get_file_content(filename: str):
    """Get content of a specific file."""
    filepath = os.path.join(FEEDBACK_DIR, filename)
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return {"content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

@app.post("/api/rate/{filename}")
async def rate_file(filename: str, action: str = Query(...)):
    """Handle rating action for a file."""
    filepath = os.path.join(FEEDBACK_DIR, filename)
    
    try:
        if action == "good":
            # Move to train directory with next number
            next_num = get_next_train_number()
            new_filename = f"{next_num:04d}.md"
            new_filepath = os.path.join(TRAIN_DIR, new_filename)
            shutil.move(filepath, new_filepath)
        elif action == "bad":
            # Move to trash directory
            trash_filepath = os.path.join(TRASH_DIR, filename)
            shutil.move(filepath, trash_filepath)
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        # Return next file in list
        files = get_feedback_files()
        next_file = files[0] if files else None
        return {"next": os.path.basename(next_file) if next_file else None}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to move file: {str(e)}")

@app.get("/")
async def serve_interface():
    """Serve the main interface."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "verify_template.html")
    with open(template_path, "r") as f:
        html = f.read()
    return HTMLResponse(content=html)

def main():
    global FEEDBACK_DIR, TRAIN_DIR, TRASH_DIR
    
    parser = argparse.ArgumentParser(description='Verify training examples')
    parser.add_argument('feedback_dir', help='Directory containing feedback files')
    parser.add_argument('train_dir', help='Directory containing training files')
    parser.add_argument('--trash-dir', default='trash', help='Directory for rejected files')
    parser.add_argument('--port', type=int, default=8000, help='Port to serve on')
    
    args = parser.parse_args()
    
    FEEDBACK_DIR = args.feedback_dir
    TRAIN_DIR = args.train_dir
    TRASH_DIR = args.trash_dir
    
    # Create trash directory if it doesn't exist
    os.makedirs(TRASH_DIR, exist_ok=True)
    
    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()
