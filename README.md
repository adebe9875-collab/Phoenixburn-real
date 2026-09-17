# PhoenixBurn REAL — ISO to USB Burner

## About The Project
PhoenixBurn REAL is a functional ISO-to-USB drive burner created as part of the **ALphoenixa OS / dstc** project. It allows users to create bootable USB flash drives directly from ISO image files through a secure command-line interface.

## Language & Technologies Used
- **Programming Language:** Python 3 (Pure Python 3.7+)
- **Target Operating System:** Linux (Ubuntu, Debian, Mint, Fedora, etc.)
- **System Utilities Used:** `lsblk` (drive detection), `dd` (raw data writing), and `umount` (unmounting partitions).

## How It Works
1. **Drive Filtering:** Scans system block devices and isolates removable USB drives while automatically hiding internal hard drives and system partitions (`/`, `/boot`, `/home`, `[SWAP]`).
2. **User Input & Validation:** Prompts for the ISO file path and lets the user select the target USB drive.
3. **Safety Verification:** Requires two explicit confirmations (typing the exact device path and typing `YES`) to prevent accidental data loss.
4. **Partition Unmounting & Writing:** Automatically unmounts active USB partitions and streams the ISO data directly to the raw block device with real-time progress reporting.

## Key Features
- **Direct Raw Writing:** Fast and reliable ISO burning directly to USB devices.
- **Advanced Safety Controls:** Protection against overwriting system or internal drives.
- **Multilingual Support:** Interactive CLI supporting English, Arabic, French, and German.
- **Real-Time Progress Tracking:** Shows written data size, total size, and percentage during the burn process.

## How to Run
sudo python3 phoenixburn_real.py
1. Open your Linux Terminal and navigate to the directory where `phoenixburn_real.py` is saved:
   ```bash
   cd /path/to/script/directory
