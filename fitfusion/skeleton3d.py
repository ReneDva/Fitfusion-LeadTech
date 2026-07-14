"""Procedural 3D stick-figure exercise demos (Plotly).

Not a photorealistic rigged avatar — that needs a real 3D asset/animation pipeline, out of
scope for a local Python app (see README roadmap). This gives a genuinely interactive,
rotatable (drag with mouse), animated 3D demonstration of the movement pattern and which
muscles are active, generated entirely from coordinates — no external 3D assets required.
"""
import plotly.graph_objects as go

BASE_POSE = {
    "head": (0, 1.7, 0),
    "neck": (0, 1.5, 0),
    "l_shoulder": (-0.22, 1.45, 0),
    "r_shoulder": (0.22, 1.45, 0),
    "l_elbow": (-0.38, 1.15, 0),
    "r_elbow": (0.38, 1.15, 0),
    "l_wrist": (-0.42, 0.85, 0),
    "r_wrist": (0.42, 0.85, 0),
    "spine_base": (0, 0.9, 0),
    "l_hip": (-0.13, 0.9, 0),
    "r_hip": (0.13, 0.9, 0),
    "l_knee": (-0.15, 0.5, 0),
    "r_knee": (0.15, 0.5, 0),
    "l_ankle": (-0.16, 0.05, 0),
    "r_ankle": (0.16, 0.05, 0),
}

BONES = [
    ("head", "neck"), ("neck", "l_shoulder"), ("neck", "r_shoulder"),
    ("l_shoulder", "l_elbow"), ("l_elbow", "l_wrist"),
    ("r_shoulder", "r_elbow"), ("r_elbow", "r_wrist"),
    ("neck", "spine_base"), ("spine_base", "l_hip"), ("spine_base", "r_hip"),
    ("l_hip", "l_knee"), ("l_knee", "l_ankle"),
    ("r_hip", "r_knee"), ("r_knee", "r_ankle"),
    ("l_shoulder", "r_shoulder"), ("l_hip", "r_hip"),
]

# Each entry: (pose_b overrides, active muscles, short cue)
EXERCISE_LIBRARY = {
    "squat": (
        {
            "spine_base": (0, 0.55, 0.05), "neck": (0, 1.15, 0.05), "head": (0, 1.35, 0.05),
            "l_hip": (-0.13, 0.55, 0.05), "r_hip": (0.13, 0.55, 0.05),
            "l_knee": (-0.18, 0.32, 0.18), "r_knee": (0.18, 0.32, 0.18),
            "l_shoulder": (-0.22, 1.1, 0.05), "r_shoulder": (0.22, 1.1, 0.05),
            "l_elbow": (-0.35, 0.95, 0.3), "r_elbow": (0.35, 0.95, 0.3),
            "l_wrist": (-0.4, 0.95, 0.55), "r_wrist": (0.4, 0.95, 0.55),
        },
        ["quads", "glutes", "hamstrings"], "Hips back and down, chest up, knees tracking over toes.",
    ),
    "pushup": (
        {
            "l_elbow": (-0.38, 0.95, 0), "r_elbow": (0.38, 0.95, 0),
            "l_shoulder": (-0.22, 1.05, 0), "r_shoulder": (0.22, 1.05, 0),
            "neck": (0, 1.1, 0), "head": (0, 1.25, 0.02),
        },
        ["chest", "triceps", "shoulders", "core"], "Straight line from head to heels, elbows at ~45°.",
    ),
    "bicep_curl": (
        {
            "l_elbow": (-0.38, 1.15, 0), "r_elbow": (0.38, 1.15, 0),
            "l_wrist": (-0.3, 1.45, 0.1), "r_wrist": (0.3, 1.45, 0.1),
        },
        ["biceps"], "Elbows pinned to your sides, curl with control — no swinging.",
    ),
    "lunge": (
        {
            "l_hip": (-0.13, 0.65, 0), "r_hip": (0.13, 0.65, -0.25),
            "spine_base": (0, 0.65, -0.05), "neck": (0, 1.25, -0.05), "head": (0, 1.45, -0.05),
            "l_knee": (-0.14, 0.3, 0.25), "l_ankle": (-0.15, 0.05, 0.35),
            "r_knee": (0.16, 0.35, -0.35), "r_ankle": (0.16, 0.05, -0.45),
        },
        ["quads", "glutes", "hamstrings"], "Front knee over ankle, back knee lowers toward the floor.",
    ),
    "plank": (
        {
            "l_elbow": (-0.38, 0.9, 0.1), "r_elbow": (0.38, 0.9, 0.1),
            "l_wrist": (-0.4, 0.9, 0.25), "r_wrist": (0.4, 0.9, 0.25),
            "l_shoulder": (-0.22, 1.0, 0), "r_shoulder": (0.22, 1.0, 0),
            "spine_base": (0, 0.95, -0.3), "neck": (0, 1.0, -0.55), "head": (0, 1.0, -0.75),
            "l_hip": (-0.13, 0.95, -0.3), "r_hip": (0.13, 0.95, -0.3),
            "l_knee": (-0.14, 0.5, -0.55), "r_knee": (0.14, 0.5, -0.55),
            "l_ankle": (-0.15, 0.1, -0.8), "r_ankle": (0.15, 0.1, -0.8),
        },
        ["core", "shoulders"], "Squeeze glutes and core — hips level, no sagging.",
    ),
    "jumping_jack": (
        {
            "l_wrist": (-0.55, 1.75, 0), "r_wrist": (0.55, 1.75, 0),
            "l_elbow": (-0.5, 1.5, 0), "r_elbow": (0.5, 1.5, 0),
            "l_shoulder": (-0.3, 1.5, 0), "r_shoulder": (0.3, 1.5, 0),
            "l_knee": (-0.3, 0.5, 0), "r_knee": (0.3, 0.5, 0),
            "l_ankle": (-0.4, 0.05, 0), "r_ankle": (0.4, 0.05, 0),
            "l_hip": (-0.2, 0.9, 0), "r_hip": (0.2, 0.9, 0),
        },
        ["full_body"], "Explosive but controlled — land softly with soft knees.",
    ),
}


def _lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _pose_at(exercise: str, t: float) -> dict:
    """t in [0,1]: 0 = start pose, 1 = full range-of-motion pose."""
    overrides, _, _ = EXERCISE_LIBRARY[exercise]
    pose = {}
    for joint, base_xyz in BASE_POSE.items():
        target_xyz = overrides.get(joint, base_xyz)
        pose[joint] = _lerp(base_xyz, target_xyz, t)
    return pose


def _trace_from_pose(pose: dict, color: str) -> tuple[go.Scatter3d, go.Scatter3d]:
    xs, ys, zs = [], [], []
    for j1, j2 in BONES:
        p1, p2 = pose[j1], pose[j2]
        xs += [p1[0], p2[0], None]
        ys += [p1[1], p2[1], None]
        zs += [p1[2], p2[2], None]
    bone_trace = go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", line=dict(color=color, width=8), hoverinfo="skip")
    jx, jy, jz = zip(*pose.values())
    joint_trace = go.Scatter3d(
        x=jx, y=jy, z=jz, mode="markers",
        marker=dict(size=6, color="#F4B223"),
        text=list(pose.keys()), hoverinfo="text",
    )
    return bone_trace, joint_trace


def build_figure(exercise: str, n_steps: int = 16) -> go.Figure:
    if exercise not in EXERCISE_LIBRARY:
        exercise = "squat"
    ts = [i / n_steps for i in range(n_steps + 1)] + [1 - i / n_steps for i in range(1, n_steps + 1)]

    bone0, joint0 = _trace_from_pose(_pose_at(exercise, ts[0]), "#4CB7C5")
    frames = []
    for i, t in enumerate(ts):
        bone, joint = _trace_from_pose(_pose_at(exercise, t), "#4CB7C5")
        frames.append(go.Frame(data=[bone, joint], name=str(i)))

    fig = go.Figure(
        data=[bone0, joint0],
        frames=frames,
        layout=go.Layout(
            paper_bgcolor="#151515",
            plot_bgcolor="#151515",
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            scene=dict(
                xaxis=dict(visible=False, range=[-1, 1]),
                yaxis=dict(visible=False, range=[-0.2, 2]),
                zaxis=dict(visible=False, range=[-1, 1]),
                aspectmode="cube",
                bgcolor="#090909",
                camera=dict(eye=dict(x=1.4, y=0.6, z=1.4)),
            ),
            updatemenus=[dict(
                type="buttons", showactive=False, x=0.05, y=0.05,
                buttons=[
                    dict(label="▶ Play", method="animate",
                         args=[None, {"frame": {"duration": 60, "redraw": True}, "fromcurrent": True, "loop": True}]),
                    dict(label="⏸ Pause", method="animate",
                         args=[[None], {"frame": {"duration": 0}, "mode": "immediate"}]),
                ],
                font=dict(color="#090909"), bgcolor="#F4B223",
            )],
        ),
    )
    return fig


def exercise_info(exercise: str) -> dict:
    overrides, muscles, cue = EXERCISE_LIBRARY.get(exercise, EXERCISE_LIBRARY["squat"])
    return {"muscles": muscles, "cue": cue}


def available_exercises() -> list[str]:
    return list(EXERCISE_LIBRARY.keys())
