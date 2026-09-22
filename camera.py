# ─── FarmGuard Camera Handler (Raspberry Pi / picamera2) ───────────────────
#
# Drop-in replacement for the original OpenCV-webcam camera.py.
# main.py calls get_camera(), read_frame(cap), release_camera(cap) exactly
# as before - this is the ONLY file that needed to change for the Pi.
#
# Requires (install via apt, not pip, on Raspberry Pi OS):
#   sudo apt install -y python3-picamera2
#
import cv2
from picamera2 import Picamera2
import config


def get_camera():
    """Opens the Pi Camera Module v2 over CSI."""
    try:
        picam = Picamera2()
        cam_config = picam.create_video_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        picam.configure(cam_config)
        picam.start()
        print("✅ Pi Camera opened successfully!")
        print("   Source: CSI Camera Module v2")
        return picam
    except Exception as e:
        print("❌ ERROR: Could not open Pi Camera!")
        print(f"   {e}")
        return None


def read_frame(cap):
    """Reads a single frame from the Pi Camera. Returns a BGR frame for
    consistency with cv2 drawing calls used elsewhere in main.py."""
    try:
        frame_rgb = cap.capture_array()
        # picamera2 delivers RGB888; main.py's cv2.rectangle/putText and
        # cv2.imwrite expect BGR, same as the original webcam path did.
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        return frame_bgr
    except Exception as e:
        print(f"❌ ERROR: Could not read frame from Pi Camera: {e}")
        return None


def release_camera(cap):
    """Cleanly stops the Pi Camera."""
    if cap is not None:
        cap.stop()
    print("📷 Camera released.")
