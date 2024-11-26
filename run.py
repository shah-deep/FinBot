import subprocess

# Run the backend server
subprocess.run("uvicorn backend.server:app --host 127.0.0.1 --port 8000", shell=True)

# Run the frontend application
subprocess.Popen("python frontend/app.py", shell=True)


