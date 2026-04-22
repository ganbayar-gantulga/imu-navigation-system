# 🧭 IMU Navigation System

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![Arduino](https://img.shields.io/badge/Arduino-MPU--6050-00979D?style=flat-square&logo=arduino&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-1.24-013243?style=flat-square&logo=numpy&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-3.7-11557C?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-In%20Progress-orange?style=flat-square)

Real-time IMU (Inertial Measurement Unit) sensor data processing and 3D orientation visualization system built with Arduino and Python. Implements a **Complementary Filter** to fuse accelerometer and gyroscope data for stable orientation estimation.

---

## 📺 Demo

> 3D orientation visualization — MPU-6050 simulation mode

![Demo](assets/demo.gif)

---

## 🎯 Project Overview

| | |
|---|---|
| **Sensor** | MPU-6050 (Accelerometer + Gyroscope) |
| **Algorithm** | Complementary Filter (α = 0.96) |
| **Interface** | Arduino → Python Serial |
| **Visualization** | Real-time 3D + 2D graphs |
| **Mode** | Simulation & Hardware ready |

---

## 🧠 How It Works

```
MPU-6050 Sensor (Arduino)
        │
        │  Serial (9600 baud)
        ▼
  serial_reader.py
        │
        ▼
┌───────────────────────┐
│   Complementary Filter │
│                        │
│  angle = α × (angle + gyro × dt)   │
│        + (1-α) × acc_angle         │
│                        │
│  Gyroscope  → 96% weight (fast)    │
│  Accelerometer → 4% weight (stable)│
└───────────────────────┘
        │
        ▼
  3D Visualization + CSV Logger
```

### Why Complementary Filter?

| Sensor | Advantage | Disadvantage |
|---|---|---|
| Accelerometer | No drift, stable long-term | Noisy, slow response |
| Gyroscope | Fast, precise short-term | Drift over time |
| **Combined** | **Fast + Stable** ✅ | — |

---

## 📁 Project Structure

```
imu-navigation-system/
│
├── 📁 arduino/
│   └── imu_reader.ino          # MPU-6050 data acquisition
│
├── 📁 python/
│   ├── simulate.py             # IMU data simulator (no hardware needed)
│   ├── filter.py               # Complementary Filter implementation
│   ├── visualizer.py           # Real-time 3D + 2D visualization
│   └── main.py                 # Entry point — ties all modules together
│
├── 📁 data/
│   └── session_*.csv           # Logged IMU sessions
│
├── 📁 notebooks/
│   └── analysis.ipynb          # EDA + filter comparison
│
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone git@github.com:ganbayar-gantulga/imu-navigation-system.git
cd imu-navigation-system

conda create -n imu-nav python=3.11
conda activate imu-nav

conda install numpy matplotlib scipy -y
pip install pyserial
```

### 2. Run — Simulation Mode (No Hardware)

```bash
python python/main.py --mode simulate
```

### 3. Run — Arduino Mode (Hardware)

```bash
# Upload arduino/imu_reader.ino to your Arduino first
python python/main.py --mode arduino --port COM3
```

### 4. Save Data to CSV

```bash
python python/main.py --mode simulate --save
```

---

## 📊 Visualization

The system displays real-time data in a dashboard:

```
┌─────────────────┬──────────────────┐
│                 │  ROLL   +23.4°   │
│   3D Board      │  PITCH  -12.1°   │
│   (rotating)    │  YAW    +45.2°   │
│                 │                  │
├────────┬────────┤                  │
│  Roll  │ Pitch  │                  │
├────────┴────────┴──────────────────┤
│  Yaw                               │
└────────────────────────────────────┘
```

---

## 🔌 Arduino Wiring (MPU-6050)

| MPU-6050 | Arduino Uno |
|---|---|
| VCC | 5V |
| GND | GND |
| SCL | A5 |
| SDA | A4 |

---

## 📈 Filter Performance

The Complementary Filter closely tracks true orientation:

```
   Time |   Roll (filtered) | Roll (true)  | Error
--------|--------------------|--------------|-------
   0.10 |          +5.23°   |     +5.89°   | 0.66°
   0.50 |         +18.45°   |    +18.92°   | 0.47°
   1.00 |         +29.12°   |    +29.34°   | 0.22°
```

---

## 🗺️ Roadmap

- [x] IMU data simulator
- [x] Complementary Filter
- [x] Real-time 3D visualization
- [x] CSV data logger
- [ ] Arduino hardware integration
- [ ] Kalman Filter comparison
- [ ] Jupyter notebook analysis
- [ ] Magnetometer (Yaw drift correction)

---

## 📚 Key Concepts Learned

- **Hardware-Software integration** — Arduino ↔ Python Serial communication
- **Signal processing** — Sensor fusion with Complementary Filter
- **Real-time systems** — Live data streaming and visualization
- **Rotation mathematics** — Euler angles and rotation matrices

---

## 👤 Author

**Ganbayar Gantulga**
[GitHub](https://github.com/ganbayar-gantulga) · [Portfolio](https://github.com/ganbayar-gantulga?tab=repositories)

---

## 📄 License

MIT License — feel free to use and modify.
