# ALphoenixa OS

ALphoenixa OS is a web-based operating system simulation that runs entirely inside any modern web browser using HTML5, CSS3, and JavaScript. It provides a Linux/Debian-like desktop environment featuring an interactive start menu, taskbar, file manager, simulated browser, and terminal interface without requiring any installation.

The system also includes **PhoenixBurn**, a tool suite designed to simulate and handle ISO-to-USB image burning.

---

## Features

- **Virtual Desktop Environment:** Interactive window management with draggable windows, taskbar, and application menu.
- **Simulated Terminal:** Practice Linux commands in a safe, isolated browser environment.
- **Built-in PhoenixBurn Tools:**
  - `phoenixburn.py`: Safe CLI simulator for learning how ISO burning works.
  - `phoenixburn_real.py`: Functional Linux CLI tool to burn real ISO images to USB drives using `dd`.

---

## How to Run

### 1. Run ALphoenixa OS
Open `index.html` in any web browser or host it on a local server.

### 2. Run PhoenixBurn Simulator
Execute the safe simulation script:
```bash
python3 phoenixburn.py
