"""
simulate.py
-----------
MPU-6050 мэдрэгчийг дуурайсан IMU simulator.
Hardware байхгүй үед бодит sensor шиг өгөгдөл гаргана.

Сурах зорилго:
    - IMU өгөгдөл ямар бүтэцтэй байдгийг ойлгох
    - Accelerometer ба Gyroscope ялгааг мэдэх
    - Шуугиан (noise) бодит мэдрэгчид хэрхэн байдгийг харах
"""

import numpy as np
import time


class IMUSimulator:
    """
    MPU-6050 IMU мэдрэгчийг дуурайдаг класс.

    Attributes:
        sample_rate (int): Секундэд хэдэн удаа өгөгдөл авах (Hz)
        noise_level (float): Шуугианы хэмжээ (жижиг = цэвэр, том = шуугиантай)
    """

    def __init__(self, sample_rate=100, noise_level=0.02):
        self.sample_rate = sample_rate          # 100 Hz = MPU-6050-ийн өгөгдөл
        self.noise_level = noise_level
        self.dt = 1.0 / sample_rate             # Хоёр хэмжилтийн хоорондох цаг
        self.t = 0.0                            # Нийт өнгөрсөн цаг

        # Бодит өнцгийн утга (simulator дотроо мэддэг "үнэн" утга)
        self.true_roll  = 0.0
        self.true_pitch = 0.0
        self.true_yaw   = 0.0

        print(f"IMU Simulator эхэллээ: {sample_rate}Hz, noise={noise_level}")
        print("-" * 50)

    def _noise(self):
        """Бодит мэдрэгчийн шуугианыг дуурайна."""
        return np.random.normal(0, self.noise_level)

    def _update_true_angles(self):
        """
        Хөдөлгөөний загвар — нисгэгч нарийн хөдөлгөөн хийж байгааг дуурайна.
        sin/cos ашиглан жигд, давтагдах хөдөлгөөн үүсгэнэ.
        """
        self.true_roll  = 30 * np.sin(0.4 * self.t) + 10 * np.sin(1.1 * self.t)
        self.true_pitch = 20 * np.cos(0.3 * self.t) +  8 * np.sin(0.8 * self.t)
        self.true_yaw   = 15 * self.t              + 12 * np.sin(0.5 * self.t)

    def read(self):
        """
        MPU-6050-ийн нэг хэмжилтийг дуурайна.

        Returns:
            dict: {
                'accel': {'x', 'y', 'z'}  → g нэгжээр (1g = 9.8 m/s²)
                'gyro':  {'x', 'y', 'z'}  → градус/секунд
                'timestamp': float         → секунд
            }

        Тайлбар:
            Accelerometer → хүндийн хүчний чиглэлийг хэмждэг
            Gyroscope     → эргэлтийн хурдыг хэмждэг
        """
        self._update_true_angles()

        # Радиан руу хөрвүүлэх
        r = np.radians(self.true_roll)
        p = np.radians(self.true_pitch)

        # ── Accelerometer ──────────────────────────────────────────────
        # Хүндийн хүч (gravity) мэдрэгчид хэрхэн харагдахыг тооцоолно
        # Тогтуун байрлалд: ax=0, ay=0, az=1g
        ax = -np.sin(p)                          + self._noise()
        ay =  np.sin(r) * np.cos(p)              + self._noise()
        az =  np.cos(r) * np.cos(p)              + self._noise()

        # ── Gyroscope ──────────────────────────────────────────────────
        # Өнцгийн өөрчлөлтийн хурд (°/s) + бага зэрэг drift шуугиан
        gx = 30 * 0.4 * np.cos(0.4 * self.t) + 10 * 1.1 * np.cos(1.1 * self.t) + self._noise() * 3
        gy = -20 * 0.3 * np.sin(0.3 * self.t) + 8 * 0.8 * np.cos(0.8 * self.t) + self._noise() * 3
        gz = 15                                 + 12 * 0.5 * np.cos(0.5 * self.t) + self._noise() * 3

        self.t += self.dt

        return {
            'accel': {'x': round(ax, 4), 'y': round(ay, 4), 'z': round(az, 4)},
            'gyro':  {'x': round(gx, 4), 'y': round(gy, 4), 'z': round(gz, 4)},
            'timestamp': round(self.t, 4),
            # Шалгалтын зорилгоор "үнэн" өнцгийг хадгална
            '_true_angles': {
                'roll':  round(self.true_roll,  2),
                'pitch': round(self.true_pitch, 2),
                'yaw':   round(self.true_yaw,   2),
            }
        }

    def stream(self, duration=None):
        """
        Тасралтгүй өгөгдлийн урсгал үүсгэнэ (generator).

        Args:
            duration (float|None): Хэдэн секунд ажиллах. None = үүрд.

        Хэрэглэх жишээ:
            for data in imu.stream(duration=5):
                print(data)
        """
        start = time.time()
        while True:
            yield self.read()
            time.sleep(self.dt)

            if duration and (time.time() - start) >= duration:
                break


# ── Туршилтын горим ────────────────────────────────────────────────────────
if __name__ == "__main__":
    imu = IMUSimulator(sample_rate=10, noise_level=0.02)

    print("IMU өгөгдөл уншиж байна... (Ctrl+C дарж зогсоо)\n")
    print(f"{'Цаг':>8} | {'AX':>8} {'AY':>8} {'AZ':>8} | {'GX':>8} {'GY':>8} {'GZ':>8}")
    print("-" * 70)

    try:
        for data in imu.stream(duration=5):
            a = data['accel']
            g = data['gyro']
            t = data['timestamp']
            print(f"{t:>8.2f} | {a['x']:>8.4f} {a['y']:>8.4f} {a['z']:>8.4f} | {g['x']:>8.4f} {g['y']:>8.4f} {g['z']:>8.4f}")

    except KeyboardInterrupt:
        print("\nЗогссон.")

    print("\n✅ simulate.py амжилттай ажиллаж байна!")
