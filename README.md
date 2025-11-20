# 🛡️ Neral VRAM Guard

**Neral VRAM Guard** is a lightweight, standalone Python utility designed to monitor NVIDIA GPU memory usage and automatically manage Ollama models.

When your VRAM usage exceeds a safe threshold, the script forces Ollama to unload models immediately—preventing system freezes, OOM (Out of Memory) crashes, and performance drops during heavy AI workflows.

---

## 🚀 Features

* **Real-Time Monitoring** – Checks VRAM usage using `nvidia-smi` at regular intervals.
* **Auto-Unload** – Automatically detects loaded Ollama models and unloads them when memory is high.
* **Panic Button** – Use `--clear-now` to instantly free VRAM.
* **Dry Run Mode** – Simulate cleanup logic without actually unloading models.
* **Lightweight** – Minimal dependencies (only requires `aiohttp`).

---

## 📋 Prerequisites

* Python **3.8+**
* NVIDIA GPU with drivers installed and `nvidia-smi` in PATH
* Ollama installed and running locally

---

## 🛠️ Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/neral-vram-guard.git
cd neral-vram-guard
```

Install the dependency:

```bash
pip install aiohttp
```

---

## 📖 Usage

### 1. Standard Guard Mode

Run the script in the background to keep your system protected.
By default, it checks every 5 seconds and unloads models if VRAM exceeds **20GB (20480 MB)**.

```bash
python vram_guard.py
```

### 2. Custom Thresholds

Set limits tailored for your GPU.
Example: limit set to **10GB** while checking every **2 seconds**:

```bash
python vram_guard.py --threshold 10240 --interval 2
```

### 3. Panic Button (Immediate Cleanup)

Free VRAM instantly if you need resources for gaming, rendering, or other heavy tasks:

```bash
python vram_guard.py --clear-now
```

### 4. Dry Run (Safe Testing)

Simulate cleanup actions without actually unloading models:

```bash
python vram_guard.py --threshold 5000 --dry-run
```

---

## ⚙️ Configuration Arguments

| Argument      | Default                                          | Description                                    |
| ------------- | ------------------------------------------------ | ---------------------------------------------- |
| `--threshold` | 20480                                            | VRAM limit in MB. Exceeding it unloads models. |
| `--interval`  | 5                                                | How often (seconds) to check VRAM usage.       |
| `--host`      | [http://localhost:11434](http://localhost:11434) | URL where Ollama is running.                   |
| `--clear-now` | False                                            | Instantly unload all models and exit.          |
| `--dry-run`   | False                                            | Log actions without unloading models.          |

---

## 🤖 How It Works

1. Executes `nvidia-smi` to retrieve current VRAM usage.
2. If usage exceeds the `--threshold`, it queries Ollama's `/api/ps` to detect active models.
3. For each model, it sends a `/api/generate` request with `keep_alive: 0`, signaling Ollama to free VRAM immediately.

---

## 📄 License

Licensed under the **MIT License**. See the `LICENSE` file for full details.
