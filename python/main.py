"""
main.py
-------
IMU Navigation System — төслийн үндсэн файл.
Бүх модулийг нэгтгэж ажиллуулна.

Хэрэглэх:
    python main.py --mode simulate       # Hardware байхгүй
    python main.py --mode arduino        # Arduino холбосон үед
    python main.py --mode simulate --save # CSV-д хадгалах
"""

import argparse
import csv
import os
import time
from datetime import datetime

from simulate import IMUSimulator
from filter import ComplementaryFilter
from visualizer import IMUVisualizer


# ── Тохиргоо ──────────────────────────────────────────────────────────────
SAMPLE_RATE = 50       # Hz
ALPHA       = 0.96     # Complementary filter жин
DATA_DIR    = os.path.join(os.path.dirname(__file__), '..', 'data')


# ── Arduino горим ─────────────────────────────────────────────────────────
def read_arduino(port='COM3', baudrate=9600):
    """
    Arduino-с serial өгөгдөл уншина.
    Hardware ирэхэд энэ функцийг ашиглана.

    Arduino Serial.println() форматтай тохирно:
        "ax,ay,az,gx,gy,gz"
        Жишээ: "0.01,0.02,0.98,1.23,-0.45,0.12"

    Args:
        port (str): COM port — Windows: 'COM3', Mac/Linux: '/dev/ttyUSB0'
        baudrate (int): Arduino-ийн Serial.begin()-тэй тохирох ёстой
    """
    try:
        import serial
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Arduino reset хийх хугацаа
        print(f"✅ Arduino холбогдлоо: {port} @ {baudrate}bps")

        while True:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue
            try:
                ax, ay, az, gx, gy, gz = map(float, line.split(','))
                yield {
                    'accel': {'x': ax, 'y': ay, 'z': az},
                    'gyro':  {'x': gx, 'y': gy, 'z': gz},
                    'timestamp': time.time(),
                }
            except ValueError:
                continue  # Буруу форматтай мөрийг алгасна

    except ImportError:
        print("❌ pyserial суугаагүй байна: pip install pyserial")
    except Exception as e:
        print(f"❌ Arduino холбогдсонгүй: {e}")
        print("   Simulation горим руу шилжиж байна...\n")


# ── CSV Logger ─────────────────────────────────────────────────────────────
class DataLogger:
    """
    IMU өгөгдлийг CSV файлд хадгална.
    Дараа нь notebooks/analysis.ipynb-д ашиглана.
    """

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.path = os.path.join(DATA_DIR, f'session_{timestamp}.csv')

        self.file = open(self.path, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow([
            'timestamp',
            'accel_x', 'accel_y', 'accel_z',
            'gyro_x',  'gyro_y',  'gyro_z',
            'roll',    'pitch',   'yaw',
        ])
        print(f"📁 Өгөгдөл хадгалж байна: {self.path}")

    def log(self, imu_data, angles):
        """Нэг хэмжилтийг бичнэ."""
        a = imu_data['accel']
        g = imu_data['gyro']
        self.writer.writerow([
            imu_data['timestamp'],
            a['x'], a['y'], a['z'],
            g['x'], g['y'], g['z'],
            angles['roll'], angles['pitch'], angles['yaw'],
        ])

    def close(self):
        self.file.close()
        print(f"\n✅ Хадгалагдлаа: {self.path}")


# ── Console горим (visualization байхгүй) ─────────────────────────────────
def run_console(source, save=False):
    """
    Зөвхөн terminal дээр өгөгдөл хэвлэнэ.
    Visualization шаардахгүй — server эсвэл debug горим.
    """
    filt   = ComplementaryFilter(alpha=ALPHA)
    logger = DataLogger() if save else None
    prev_t = 0.0

    print(f"\n{'Цаг':>8} | {'Roll':>9} {'Pitch':>9} {'Yaw':>9}")
    print("-" * 45)

    try:
        for data in source:
            t  = data['timestamp']
            dt = t - prev_t if prev_t > 0 else 1 / SAMPLE_RATE
            prev_t = t

            angles = filt.update(data['accel'], data['gyro'], dt)

            print(
                f"{t:>8.2f} | "
                f"{angles['roll']:>+8.2f}° "
                f"{angles['pitch']:>+8.2f}° "
                f"{angles['yaw']:>+8.2f}°"
            )

            if logger:
                logger.log(data, angles)

    except KeyboardInterrupt:
        print("\n⏹  Зогссон.")
    finally:
        if logger:
            logger.close()


# ── Үндсэн функц ──────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description='IMU Navigation System',
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        '--mode',
        choices=['simulate', 'arduino'],
        default='simulate',
        help=(
            'simulate → Hardware байхгүй, дуурайлган ажиллана\n'
            'arduino  → Arduino-с бодит өгөгдөл уншина'
        ),
    )
    parser.add_argument(
        '--port',
        default='COM3',
        help='Arduino COM port (зөвхөн --mode arduino горимд хэрэгтэй)',
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Өгөгдлийг data/ folder-т CSV хэлбэрээр хадгална',
    )
    parser.add_argument(
        '--no-viz',
        action='store_true',
        help='Visualization байхгүйгээр зөвхөн terminal горимд ажиллана',
    )
    args = parser.parse_args()

    # ── Гарчиг ──────────────────────────────────────────────────────────
    print("=" * 55)
    print("   IMU NAVIGATION SYSTEM")
    print(f"   Mode : {args.mode.upper()}")
    print(f"   Save : {'Тийм' if args.save else 'Үгүй'}")
    print(f"   Viz  : {'Үгүй' if args.no_viz else '3D + Graph'}")
    print("=" * 55)

    # ── Өгөгдлийн эх сурвалж сонгох ─────────────────────────────────────
    if args.mode == 'simulate':
        print("\n🔵 Simulation горим — MPU-6050 дуурайлга\n")
        imu = IMUSimulator(sample_rate=SAMPLE_RATE, noise_level=0.02)
        source = imu.stream()
    else:
        print(f"\n🟢 Arduino горим — {args.port} port\n")
        source = read_arduino(port=args.port)

    # ── Ажиллуулах ──────────────────────────────────────────────────────
    if args.no_viz:
        run_console(source, save=args.save)
    else:
        # Visualization горим — save нэмж хийх
        if args.save:
            # Visualizer дотор logger нэмнэ
            viz    = IMUVisualizer()
            logger = DataLogger()

            orig_update = viz.update
            def update_with_log(frame):
                orig_update(frame)
                if viz.history['time']:
                    # Сүүлчийн утгыг хадгална
                    imu_data = viz.imu.read()
                    angles = {
                        'roll':  viz.history['roll'][-1],
                        'pitch': viz.history['pitch'][-1],
                        'yaw':   viz.history['yaw'][-1],
                    }
                    logger.log(imu_data, angles)

            viz.update = update_with_log
            try:
                viz.run()
            finally:
                logger.close()
        else:
            viz = IMUVisualizer()
            viz.run()


if __name__ == "__main__":
    main()
