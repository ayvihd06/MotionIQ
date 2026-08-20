"""
Batch re-encode existing annotated videos from MPEG-4 Part 2 (FMP4/mp4v)
to H.264 (browser-compatible). Run once after the fix is deployed.
"""
import imageio_ffmpeg, subprocess, shutil, cv2
from pathlib import Path

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
video_dir = Path('storage/annotated_videos')

H264_CODECS = {'avc1', 'h264', 'H264', 'X264'}

# Find all files needing re-encoding
fmp4_files = []
for f in sorted(video_dir.glob('*.mp4'), key=lambda p: p.stat().st_mtime, reverse=True):
    cap = cv2.VideoCapture(str(f))
    fi = int(cap.get(cv2.CAP_PROP_FOURCC))
    fs = ''.join([chr((fi >> 8*i) & 0xFF) for i in range(4)])
    cap.release()
    if fs.strip('\x00') not in H264_CODECS:
        fmp4_files.append((f, fs))

print(f'Found {len(fmp4_files)} videos needing H.264 re-encode')

# Re-encode most recent 5 for immediate testing
for f, codec in fmp4_files[:5]:
    print(f'Re-encoding {f.name} (codec={codec})...')
    tmp = f.with_suffix('.tmp.mp4')
    shutil.move(str(f), str(tmp))
    cmd = [
        ffmpeg_exe, '-y',
        '-i', str(tmp),
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        '-an',
        str(f)
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=120)
    if r.returncode == 0:
        tmp.unlink(missing_ok=True)
        size_mb = round(f.stat().st_size / 1024 / 1024, 2)
        print(f'  OK: {size_mb} MB')
    else:
        shutil.move(str(tmp), str(f))
        err = r.stderr.decode(errors='replace')[-300:]
        print(f'  FAILED: {err}')

print('Done.')
