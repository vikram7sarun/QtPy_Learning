# main.py
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict
import subprocess
import json
from datetime import datetime
import tempfile
import os
import shutil

app = FastAPI()

# Configure CORS with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze")
async def analyze_code(
        file: UploadFile = File(...),
        analyzers: str = Form(...)  # Receive analyzers as form data
):
    try:
        # Validate file type
        if not file.filename.endswith('.py'):
            return JSONResponse(
                status_code=400,
                content={"error": "Only Python files are supported"}
            )

        # Parse analyzers from string to list
        analyzer_list = json.loads(analyzers)

        # Create temp directory for file
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, file.filename)

            # Save uploaded file
            with open(file_path, 'wb') as buffer:
                shutil.copyfileobj(file.file, buffer)

            results = {}
            for analyzer in analyzer_list:
                try:
                    if analyzer == "pylint":
                        result = subprocess.run(
                            ["pylint", "--output-format=json", file_path],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        results["pylint"] = {"raw": result.stdout or result.stderr}

                    elif analyzer == "flake8":
                        result = subprocess.run(
                            ["flake8", file_path],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        results["flake8"] = {"raw": result.stdout or result.stderr}

                    elif analyzer == "radon":
                        cc_result = subprocess.run(
                            ["radon", "cc", "-j", file_path],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        mi_result = subprocess.run(
                            ["radon", "mi", "-j", file_path],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        results["radon"] = {
                            "raw": f"Complexity:\n{cc_result.stdout}\nMaintainability:\n{mi_result.stdout}"
                        }

                    elif analyzer == "bandit":
                        result = subprocess.run(
                            ["bandit", "-f", "json", "-r", file_path],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        results["bandit"] = {"raw": result.stdout or result.stderr}

                except subprocess.TimeoutExpired:
                    results[analyzer] = {"error": f"{analyzer} analysis timed out"}
                except Exception as e:
                    results[analyzer] = {"error": str(e)}

        return {
            "timestamp": datetime.now().isoformat(),
            "filename": file.filename,
            "results": results
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}