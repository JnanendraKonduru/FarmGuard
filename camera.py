# ─── FarmGuard Camera Handler ───────────────────────────────────────────────
import cv2
import config

def get_camera():
    """Opens the camera source defined in config.py"""
    cap = cv2.VideoCapture(config.CAMERA_SOURCE)

    if not cap.isOpened():
        print("❌ ERROR: Could not open camera!")
        print("Make sure your webcam is connected and not used by another app.")
        return None

    print(f"✅ Camera opened successfully!")
    print(f"   Source: {config.CAMERA_SOURCE}")
    return cap

def read_frame(cap):
    """Reads a single frame from the camera"""
    ret, frame = cap.read()
    if not ret:
        print("❌ ERROR: Could not read frame from camera")
        return None
    return frame

def release_camera(cap):
    """Cleanly closes the camera"""
    cap.release()
    cv2.destroyAllWindows()
    print("📷 Camera released.")