"""
visualizer.py
-------------
Real-time IMU өгөгдлийг 3D куб + 2D график хэлбэрээр харуулна.
Matplotlib ашигладаг тул extra library шаардахгүй.

Сурах зорилго:
    - Matplotlib-ийн animation ойлгох
    - 3D rotation matrix хэрхэн ажилладгийг мэдэх
    - Real-time data visualization техник сурах
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from simulate import IMUSimulator
from filter import ComplementaryFilter


# ── Тохиргоо ──────────────────────────────────────────────────────────────
SAMPLE_RATE  = 50          # Hz
HISTORY_LEN  = 100         # Графикт хэдэн утга харуулах
ALPHA        = 0.96        # Complementary filter жин


# ── 3D Куб үүсгэх ─────────────────────────────────────────────────────────
def make_cube():
    """
    MPU-6050 board-ийг дуурайсан 3D куб үүсгэнэ.
    8 оройтой, 6 талтай.

    Returns:
        vertices: (8, 3) хэмжээний массив — кубын 8 орой
        faces:    6 талын орой индексүүд
    """
    # Кубын 8 орой (x, y, z)
    vertices = np.array([
        [-1, -0.2, -1.5],   # 0: зүүн-доод-урд
        [+1, -0.2, -1.5],   # 1: баруун-доод-урд
        [+1, +0.2, -1.5],   # 2: баруун-дээд-урд
        [-1, +0.2, -1.5],   # 3: зүүн-дээд-урд
        [-1, -0.2, +1.5],   # 4: зүүн-доод-хойд
        [+1, -0.2, +1.5],   # 5: баруун-доод-хойд
        [+1, +0.2, +1.5],   # 6: баруун-дээд-хойд
        [-1, +0.2, +1.5],   # 7: зүүн-дээд-хойд
    ], dtype=float)

    # 6 тал — дөрвөн оройн индекс
    faces = [
        [0, 1, 2, 3],   # урд
        [4, 5, 6, 7],   # хойд
        [0, 4, 7, 3],   # зүүн
        [1, 5, 6, 2],   # баруун
        [3, 2, 6, 7],   # дээд
        [0, 1, 5, 4],   # доод
    ]
    return vertices, faces


def rotation_matrix(roll, pitch, yaw):
    """
    Roll, Pitch, Yaw өнцгөөс 3D эргэлтийн матриц үүсгэнэ.

    Тайлбар:
        Матриц үржих = 3 тэнхлэгийн эргэлтийг нэгтгэх.
        Rx @ Ry @ Rz = нийт эргэлт.

    Args:
        roll, pitch, yaw: Градусаар

    Returns:
        R: (3,3) эргэлтийн матриц
    """
    r = np.radians(roll)
    p = np.radians(pitch)
    y = np.radians(yaw)

    # X тэнхлэгийн эргэлт (Roll)
    Rx = np.array([
        [1,      0,       0],
        [0, np.cos(r), -np.sin(r)],
        [0, np.sin(r),  np.cos(r)],
    ])

    # Y тэнхлэгийн эргэлт (Pitch)
    Ry = np.array([
        [ np.cos(p), 0, np.sin(p)],
        [0,          1,          0],
        [-np.sin(p), 0, np.cos(p)],
    ])

    # Z тэнхлэгийн эргэлт (Yaw)
    Rz = np.array([
        [np.cos(y), -np.sin(y), 0],
        [np.sin(y),  np.cos(y), 0],
        [0,          0,         1],
    ])

    return Rz @ Ry @ Rx


# ── Visualizer класс ───────────────────────────────────────────────────────
class IMUVisualizer:
    """
    Real-time IMU visualization.

    Бүтэц:
        ┌──────────┬──────────┐
        │  3D куб  │  Мэдээлэл│
        ├──────────┴──────────┤
        │    Roll график      │
        │    Pitch график     │
        │    Yaw график       │
        └─────────────────────┘
    """

    def __init__(self):
        self.imu    = IMUSimulator(sample_rate=SAMPLE_RATE, noise_level=0.02)
        self.filt   = ComplementaryFilter(alpha=ALPHA)
        self.prev_t = 0.0

        # Түүхийн өгөгдөл
        self.history = {
            'time':  [],
            'roll':  [],
            'pitch': [],
            'yaw':   [],
        }

        self.vertices, self.faces = make_cube()

        # Өнгөний тохиргоо
        self.face_colors = [
            '#2ecc71',  # урд   - ногоон
            '#3498db',  # хойд  - цэнхэр
            '#e74c3c',  # зүүн  - улаан
            '#f39c12',  # баруун - шар
            '#9b59b6',  # дээд  - ягаан
            '#1abc9c',  # доод  - цайвар ногоон
        ]

        self._setup_figure()

    def _setup_figure(self):
        """Matplotlib дэлгэцийг тохируулна."""
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(13, 8), facecolor='#0d1117')
        self.fig.suptitle('IMU Navigation System — Real-time Visualization',
                          color='#58a6ff', fontsize=13, fontweight='bold', y=0.98)

        # Grid тохиргоо
        gs = self.fig.add_gridspec(3, 2, hspace=0.45, wspace=0.35,
                                   left=0.08, right=0.97, top=0.93, bottom=0.06)

        # 3D куб
        self.ax3d = self.fig.add_subplot(gs[0, 0], projection='3d')
        self.ax3d.set_facecolor('#161b22')
        self.ax3d.set_title('3D Orientation', color='#8b949e', fontsize=9, pad=4)

        # Мэдээллийн талбар
        self.ax_info = self.fig.add_subplot(gs[0, 1])
        self.ax_info.set_facecolor('#161b22')
        self.ax_info.axis('off')

        # Roll, Pitch, Yaw графикууд
        graph_cfg = [
            (gs[1, :], 'Roll',  '#e74c3c'),
            (gs[2, :], 'Pitch', '#2ecc71'),
        ]
        self.ax_graphs = []
        colors = ['#e74c3c', '#2ecc71', '#3498db']
        labels = ['Roll (°)', 'Pitch (°)', 'Yaw (°)']

        # Roll + Pitch = тус тусдаа, Yaw = баруун талд
        self.ax_roll  = self.fig.add_subplot(gs[1, 0])
        self.ax_pitch = self.fig.add_subplot(gs[1, 1])
        self.ax_yaw   = self.fig.add_subplot(gs[2, :])

        for ax, lbl, col in [
            (self.ax_roll,  'Roll (°)',  '#e74c3c'),
            (self.ax_pitch, 'Pitch (°)', '#2ecc71'),
            (self.ax_yaw,   'Yaw (°)',   '#3498db'),
        ]:
            ax.set_facecolor('#161b22')
            ax.set_title(lbl, color=col, fontsize=8, pad=3)
            ax.tick_params(colors='#8b949e', labelsize=7)
            ax.grid(True, alpha=0.15, color='#30363d')
            for spine in ax.spines.values():
                spine.set_color('#30363d')

        # Мэдээллийн текст
        self.info_texts = {}
        info_items = [
            ('roll_val',  0.15, 0.78, 'ROLL',  '#e74c3c'),
            ('pitch_val', 0.15, 0.52, 'PITCH', '#2ecc71'),
            ('yaw_val',   0.15, 0.26, 'YAW',   '#3498db'),
        ]
        for key, x, y, label, color in info_items:
            self.ax_info.text(x - 0.1, y + 0.12, label,
                              transform=self.ax_info.transAxes,
                              color='#8b949e', fontsize=8, fontweight='bold')
            self.info_texts[key] = self.ax_info.text(
                x + 0.35, y,
                '---',
                transform=self.ax_info.transAxes,
                color=color, fontsize=22, fontweight='bold',
                ha='center', va='center'
            )

        self.ax_info.text(0.5, 0.05,
                          f'Filter: Complementary  α={ALPHA}',
                          transform=self.ax_info.transAxes,
                          color='#484f58', fontsize=7, ha='center')

    def _draw_cube(self, roll, pitch, yaw):
        """Кубыг өгөгдсөн өнцгөөр эргүүлж зурна."""
        self.ax3d.cla()
        self.ax3d.set_facecolor('#161b22')
        self.ax3d.set_title('3D Orientation', color='#8b949e', fontsize=9, pad=4)

        # Эргэлтийн матриц хэрэглэх
        R = rotation_matrix(roll, pitch, yaw)
        rotated = (R @ self.vertices.T).T

        # Талуудыг зур
        poly_verts = []
        for face in self.faces:
            verts = [rotated[i] for i in face]
            poly_verts.append(verts)

        poly = Poly3DCollection(poly_verts, alpha=0.85,
                                facecolors=self.face_colors,
                                edgecolors='#30363d', linewidths=0.5)
        self.ax3d.add_collection3d(poly)

        # Тэнхлэгийн сум (X=улаан, Y=ногоон, Z=цэнхэр)
        for vec, col, lbl in [
            ([1.8,0,0], '#e74c3c', 'X'),
            ([0,1.8,0], '#2ecc71', 'Y'),
            ([0,0,2.5], '#3498db', 'Z'),
        ]:
            rv = R @ np.array(vec)
            self.ax3d.quiver(0, 0, 0, rv[0], rv[1], rv[2],
                             color=col, arrow_length_ratio=0.2, linewidth=1.5)
            self.ax3d.text(rv[0]*1.1, rv[1]*1.1, rv[2]*1.1, lbl,
                           color=col, fontsize=8)

        lim = 2.2
        self.ax3d.set_xlim(-lim, lim)
        self.ax3d.set_ylim(-lim, lim)
        self.ax3d.set_zlim(-lim, lim)
        self.ax3d.set_xlabel('X', color='#e74c3c', fontsize=7)
        self.ax3d.set_ylabel('Y', color='#2ecc71', fontsize=7)
        self.ax3d.set_zlabel('Z', color='#3498db', fontsize=7)
        self.ax3d.tick_params(colors='#484f58', labelsize=6)

    def _draw_graphs(self):
        """Roll, Pitch, Yaw графикуудыг шинэчилнэ."""
        h = self.history
        if len(h['time']) < 2:
            return

        t = h['time']
        for ax, key, col in [
            (self.ax_roll,  'roll',  '#e74c3c'),
            (self.ax_pitch, 'pitch', '#2ecc71'),
            (self.ax_yaw,   'yaw',   '#3498db'),
        ]:
            ax.cla()
            ax.set_facecolor('#161b22')
            ax.plot(t, h[key], color=col, linewidth=1.2)
            ax.fill_between(t, h[key], alpha=0.1, color=col)
            ax.tick_params(colors='#8b949e', labelsize=7)
            ax.grid(True, alpha=0.15, color='#30363d')
            for spine in ax.spines.values():
                spine.set_color('#30363d')

        self.ax_roll.set_title('Roll (°)',  color='#e74c3c', fontsize=8, pad=3)
        self.ax_pitch.set_title('Pitch (°)', color='#2ecc71', fontsize=8, pad=3)
        self.ax_yaw.set_title('Yaw (°)',   color='#3498db', fontsize=8, pad=3)

    def update(self, frame):
        """Animation-ийн нэг frame шинэчлэх."""
        data = self.imu.read()
        t    = data['timestamp']
        dt   = t - self.prev_t if self.prev_t > 0 else 1 / SAMPLE_RATE
        self.prev_t = t

        angles = self.filt.update(data['accel'], data['gyro'], dt)

        # Түүхэнд нэм
        for key in ['roll', 'pitch', 'yaw']:
            self.history[key].append(angles[key])
        self.history['time'].append(t)

        # Урт хэтрэхгүйн тулд хуучин утгыг устга
        if len(self.history['time']) > HISTORY_LEN:
            for key in self.history:
                self.history[key] = self.history[key][-HISTORY_LEN:]

        # Дэлгэцийг шинэчил
        self._draw_cube(angles['roll'], angles['pitch'], angles['yaw'])
        self._draw_graphs()

        # Текст утгуудыг шинэчил
        self.info_texts['roll_val'].set_text(f"{angles['roll']:+.1f}°")
        self.info_texts['pitch_val'].set_text(f"{angles['pitch']:+.1f}°")
        self.info_texts['yaw_val'].set_text(f"{angles['yaw']:+.1f}°")

    def run(self):
        """Visualization эхлүүл."""
        print("Visualization эхэллээ — цонхыг хааж зогсоо.\n")
        ani = animation.FuncAnimation(
            self.fig,
            self.update,
            interval=1000 // SAMPLE_RATE,
            cache_frame_data=False,
        )
        plt.show()


# ── Ажиллуулах ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    viz = IMUVisualizer()
    viz.run()
