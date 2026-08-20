import urllib.request
import ssl
import os

url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
out = "app/models/pose_landmarker_lite.task"

# Bypass SSL if needed (corporate proxy environment)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    with urllib.request.urlopen(url, context=ctx) as response:
        data = response.read()
    with open(out, "wb") as f:
        f.write(data)
    print(f"Downloaded: {os.path.getsize(out)} bytes")
except Exception as e:
    print(f"Error: {e}")
