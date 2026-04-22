"""
filter.py
---------
Complementary Filter ашиглан IMU өгөгдлөөс
Roll, Pitch, Yaw өнцгийг тооцоолно.

Сурах зорилго:
    - Accelerometer-ийн давуу ба сул талыг ойлгох
    - Gyroscope-ийн давуу ба сул талыг ойлгох
    - Хоёрыг хэрхэн хослуулж нарийвчлал нэмэгдүүлэхийг мэдэх
"""

import numpy as np


class ComplementaryFilter:
    """
    Complementary Filter.

    Томьёо:
        angle = α × (angle + gyro × dt) + (1 - α) × acc_angle

        α = 0.96 гэвэл:
            96% → Gyroscope   (хурдан хариу)
             4% → Accelerometer (урт хугацааны нарийвчлал)
    """

    def __init__(self, alpha=0.96):
        """
        Args:
            alpha (float): Filter-ийн жин. 0-1 хооронд.
                0.96 = MPU-6050-д хамгийн түгээмэл утга.
        """
        self.alpha = alpha

        # Өнцгийн одоогийн утга
        self.roll  = 0.0
        self.pitch = 0.0
        self.yaw   = 0.0

        print(f"Complementary Filter: alpha={alpha}")
        print(f"  Gyroscope жин:       {alpha*100:.0f}%")
        print(f"  Accelerometer жин:   {(1-alpha)*100:.0f}%")
        print("-" * 40)

    def _accel_angles(self, ax, ay, az):
        """
        Accelerometer-ийн өгөгдлөөс Roll, Pitch өнцгийг тооцоолно.

        Тайлбар:
            Хүндийн хүч (gravity) үргэлж доош чиглэдэг.
            Мэдрэгч хэлбийхэд ax, ay, az утгууд өөрчлөгдөнө.
            atan2() функц тэр өөрчлөлтөөс өнцгийг тооцоолно.

        Args:
            ax, ay, az: Хурдатгал (g нэгжээр)

        Returns:
            roll, pitch: Градусаар
        """
        roll  = np.degrees(np.arctan2(ay, az))
        pitch = np.degrees(np.arctan2(-ax, np.sqrt(ay**2 + az**2)))
        return roll, pitch

    def update(self, accel, gyro, dt):
        """
        Нэг хэмжилтийн өгөгдлөөр өнцгийг шинэчилнэ.

        Args:
            accel (dict): {'x', 'y', 'z'} → g нэгжээр
            gyro  (dict): {'x', 'y', 'z'} → градус/секунд
            dt    (float): Өмнөх хэмжилтээс хойш өнгөрсөн цаг (секунд)

        Returns:
            dict: {'roll', 'pitch', 'yaw'} → градусаар
        """
        # 1. Accelerometer-ийн өнцөг (удаан, гэхдээ тогтвортой)
        acc_roll, acc_pitch = self._accel_angles(
            accel['x'], accel['y'], accel['z']
        )

        # 2. Gyroscope-ийн өнцгийн өөрчлөлт (хурдан, гэхдээ drift)
        gyro_roll  = self.roll  + gyro['x'] * dt
        gyro_pitch = self.pitch + gyro['y'] * dt
        gyro_yaw   = self.yaw   + gyro['z'] * dt

        # 3. Complementary Filter — хоёрыг хослуулна
        #    α  хэсэг → gyroscope   (хурдан хөдөлгөөн мэдэрнэ)
        #    (1-α) хэсэг → accelerometer (урт хугацааны алдааг засна)
        self.roll  = self.alpha * gyro_roll  + (1 - self.alpha) * acc_roll
        self.pitch = self.alpha * gyro_pitch + (1 - self.alpha) * acc_pitch
        self.yaw   = gyro_yaw   # Yaw-д accelerometer тус болохгүй (gravity босоо)

        return {
            'roll':  round(self.roll,  3),
            'pitch': round(self.pitch, 3),
            'yaw':   round(self.yaw,   3),
        }

    def reset(self):
        """Өнцгүүдийг тэглэнэ."""
        self.roll = self.pitch = self.yaw = 0.0
        print("Filter reset хийгдлээ.")


# ── Туршилтын горим ────────────────────────────────────────────────────────
if __name__ == "__main__":
    from simulate import IMUSimulator

    imu    = IMUSimulator(sample_rate=10, noise_level=0.02)
    filt   = ComplementaryFilter(alpha=0.96)

    print("\nFilter туршиж байна... (5 секунд)\n")
    print(f"{'Цаг':>6} | {'Roll(filter)':>12} {'Pitch(filter)':>13} {'Yaw(filter)':>11} | {'Roll(үнэн)':>10} {'Pitch(үнэн)':>11}")
    print("-" * 80)

    prev_t = 0.0

    for data in imu.stream(duration=5):
        t  = data['timestamp']
        dt = t - prev_t if prev_t > 0 else 0.1
        prev_t = t

        # Filter-ийг шинэчил
        angles = filt.update(data['accel'], data['gyro'], dt)

        # Үнэн өнцөгтэй харьцуул
        true = data['_true_angles']

        print(
            f"{t:>6.2f} | "
            f"{angles['roll']:>+12.2f}° "
            f"{angles['pitch']:>+12.2f}° "
            f"{angles['yaw']:>+10.2f}° | "
            f"{true['roll']:>+9.2f}° "
            f"{true['pitch']:>+10.2f}°"
        )

    print("\n✅ filter.py амжилттай ажиллаж байна!")
