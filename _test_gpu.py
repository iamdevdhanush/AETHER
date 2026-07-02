import subprocess
result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=30)
print(result.stdout[:2000] if result.stdout else result.stderr[:2000])
