# 🧩 FRAM Module Controller

The **FRAM Module Controller** is a Python-based tool designed to easily manage, read, and write data on **FRAM (Ferroelectric RAM)** modules *via a connected microcontroller*.

It provides a simple and flexible interface (both GUI and CLI) for developers, students, and hardware enthusiasts who want to interact with FRAM memory managed by a microcontroller (e.g., Teensy, Arduino).

---

## ✨ Features

* 📖 **Read / Write / Erase** – Easily store, retrieve, and delete data from FRAM.
* 💻 **Dual Interface** – Choose between a user-friendly GUI mode and a fast CLI (Terminal) mode.
* 📤 **Export** – Dump the FRAM memory contents to a file.

---

## 🛠️ Installation

The installation process consists of two steps: preparing the microcontroller and installing the PC software.

### 1. Microcontroller

First, you must flash the `arduino.cpp` sketch  onto your microcontroller (e.g., Teensy, Arduino) using the Arduino IDE or a similar tool.

### 2. PC Software

Next, clone this repository and install the required Python dependencies:

```bash
git clone https://github.com/Bleee411/FMC_Fram-Module_Controler.git
cd FMC_Fram-Module_Controler
pip install -r requirements.txt
