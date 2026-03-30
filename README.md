# dk-pilot 🚁

A high-precision autonomous navigation system for quadcopters using the DroneKit-Python library.  
This project demonstrates stable flight and precision landing in **STABILIZE mode** under extreme wind conditions (4 m/s).

---

## 🌟 Key Features

- **Manual Mode Navigation**  
  Operates entirely in STABILIZE mode using channel overrides.

- **Fixed Heading**  
  Maintains a constant Yaw (1500 PWM) throughout the flight.

- **Asymmetric Load Control**  
  Custom PID logic with higher gains when fighting wind and lower gains when returning to center.

- **Precision Landing**  
  Automated "Squeeze & Drop" logic achieving **< 1.0m error margin**.

- **Wind Estimation**  
  Dynamic compensation for external drift during descent.

---

## 🛠 System Requirements

- **Python**: 3.9  
- **Simulator**: ArduPilot SITL (Copter)  
- **Environment**: Windows (PowerShell/CMD), Linux, or macOS  

---

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/chilistyle/dk-pilot.git
cd dk-pilot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

---

## 🕹 How to Run

### 1. Start the SITL Simulator with start coordinates

```bash
sim_vehicle.py -v ArduCopter --home=0.00,0.00,0,0
```

### 2. Execute the Mission

```bash
python main.py
```

---

## 📊 Project Structure

```
dk-pilot/
├── src/
│   ├── __init__.py      # Config loader
│   ├── connection.py    # MAVLink connection & Safety checks
│   ├── navigation.py    # PID Controllers & Vector Math
│   └── mission.py       # Mission stages (Takeoff -> Flight -> Land)
├── main.py              # Entry point 
├── .env.example         # Config Template
└── requirements.txt     # Dependencies
```
---

## ⚠️ Troubleshooting
- **"Gyros inconsistent"**: Type `reboot` in the SITL console if the EKF fails to align.
- **Wind Drift**: Without increasing `ANGLE_MAX`, the drone relies heavily on the **Integral (ki)** term. If it still drifts, slightly increase `ki` in `src/navigation.py`.
- **Overshooting**: Adjust the `kd` (derivative) gain to increase braking force during high-speed approaches.

---

## 📜 License

Distributed under the MIT License.
