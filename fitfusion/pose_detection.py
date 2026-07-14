"""Live webcam pose detection + automatic rep counting (mediapipe + streamlit-webrtc).

Optional dependency stack (opencv-python, mediapipe, streamlit-webrtc, av) — these can be
heavy/finicky to install on some machines, so every call site must check POSE_AVAILABLE
and fall back to the manual counter / static form-check instead of hard-failing the page.
"""
import math
import threading

POSE_AVAILABLE = True
try:
    import cv2
    import numpy as np
    import mediapipe as mp
    from streamlit_webrtc import VideoProcessorBase
except Exception:
    POSE_AVAILABLE = False


EXERCISE_ANGLES = {
    # joint triplet (mediapipe PoseLandmark names) + thresholds for "down" vs "up"
    "squat": {"joints": ("LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE"), "down_below": 100, "up_above": 160},
    "pushup": {"joints": ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"), "down_below": 95, "up_above": 155},
    "bicep_curl": {"joints": ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"), "down_below": 50, "up_above": 150},
    "lunge": {"joints": ("LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE"), "down_below": 100, "up_above": 165},
}


def calculate_angle(a, b, c) -> float:
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    angle = abs(radians * 180.0 / math.pi)
    return 360 - angle if angle > 180 else angle


if POSE_AVAILABLE:

    class RepCounterProcessor(VideoProcessorBase):
        """Runs on a background thread per streamlit-webrtc frame callback contract."""

        def __init__(self, exercise: str = "squat") -> None:
            self.exercise = exercise
            self.stage = "up"
            self.rep_count = 0
            self.rom_samples = []
            self.lock = threading.Lock()
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
            self.pose = self.mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6)

        def set_exercise(self, exercise: str):
            with self.lock:
                self.exercise = exercise
                self.stage = "up"
                self.rep_count = 0
                self.rom_samples = []

        def snapshot(self) -> dict:
            with self.lock:
                accuracy = self._accuracy_score()
                return {"reps": self.rep_count, "stage": self.stage, "accuracy": accuracy}

        def _accuracy_score(self) -> float:
            if not self.rom_samples:
                return 0.0
            cfg = EXERCISE_ANGLES.get(self.exercise, EXERCISE_ANGLES["squat"])
            target_bottom = cfg["down_below"]
            depths = [s for s in self.rom_samples if s < target_bottom + 20]
            if not depths:
                return 55.0
            avg_depth = sum(depths) / len(depths)
            deficit = max(0, avg_depth - target_bottom)
            return round(max(40.0, 100.0 - deficit * 1.5), 1)

        def recv(self, frame):
            img = frame.to_ndarray(format="bgr24")
            img = cv2.flip(img, 1)
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb)

            if results.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    img, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(76, 183, 197), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(244, 178, 35), thickness=2),
                )
                try:
                    lm = results.pose_landmarks.landmark
                    cfg = EXERCISE_ANGLES.get(self.exercise, EXERCISE_ANGLES["squat"])
                    j1, j2, j3 = cfg["joints"]
                    p1 = (lm[getattr(self.mp_pose.PoseLandmark, j1).value].x, lm[getattr(self.mp_pose.PoseLandmark, j1).value].y)
                    p2 = (lm[getattr(self.mp_pose.PoseLandmark, j2).value].x, lm[getattr(self.mp_pose.PoseLandmark, j2).value].y)
                    p3 = (lm[getattr(self.mp_pose.PoseLandmark, j3).value].x, lm[getattr(self.mp_pose.PoseLandmark, j3).value].y)
                    angle = calculate_angle(p1, p2, p3)

                    with self.lock:
                        self.rom_samples.append(angle)
                        if len(self.rom_samples) > 200:
                            self.rom_samples = self.rom_samples[-200:]
                        if angle < cfg["down_below"]:
                            self.stage = "down"
                        if angle > cfg["up_above"] and self.stage == "down":
                            self.stage = "up"
                            self.rep_count += 1

                    cv2.putText(img, f"{int(angle)} deg", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                except (IndexError, AttributeError):
                    pass

            with self.lock:
                reps = self.rep_count
            cv2.putText(img, f"Reps: {reps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (244, 178, 35), 2)

            import av
            return av.VideoFrame.from_ndarray(img, format="bgr24")

else:
    RepCounterProcessor = None
