# shared_video.py

import threading

video_lock = threading.Lock()
latest_frame = None
