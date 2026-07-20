import os
import shutil

src = "/Users/richardgillespie/.gemini/antigravity/brain/735a8e94-9dd5-4412-afe4-b2fe949b7d1e/affine_benchmark_terminal_1784568740210.jpg"
dst_dir = os.path.join(os.path.dirname(__file__), "..", "wiki", "assets")
os.makedirs(dst_dir, exist_ok=True)
dst = os.path.join(dst_dir, "affine_benchmark_terminal.jpg")

if os.path.exists(src):
    shutil.copyfile(src, dst)
    print(f"✅ Copied image to {dst}")
else:
    print(f"⚠️ Source file not found: {src}")
