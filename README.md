# Blink-Based Cursor Movement System

Hands-free human–computer interaction system using **eye blinks and gaze tracking** for cursor control.  
Built with **MediaPipe**, **OpenCV**, and **PyAutoGUI**, this project enables left/right clicks and cursor movement without physical input devices.

---

## 🚀 Features
- Real-time gaze-based cursor movement
- Blink classification (left, right, double)
- Adaptive smoothing & deadzone filtering
- Runs on standard webcam (no IR sensors)
- Lightweight, calibration-free design

## ⚙️ Installation

```bash
git clone https://github.com/yourusername/blink-cursor-system.git
cd blink-cursor-system
pip install -r requirements.txt


## Activate Conda Environment

conda env create -f environment.yml
conda activate blink_env


## Run the main script

python src/eye_blink_cursor.py

