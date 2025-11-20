import asyncio
import aiohttp
import subprocess
import argparse
import logging
import sys
import platform
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [VRAM GUARD] - %(message)s',
    datefmt='%H:%M:%S'
)

class VRAMManager:
    def __init__(self, threshold_mb: int, ollama_url: str, interval: int, dry_run: bool):
        self.threshold_mb = threshold_mb
        self.ollama_url = ollama_url
        self.interval = interval
        self.dry_run = dry_run
        self.system = platform.system()

    async def get_vram_usage(self) -> float:
        """
        Get current VRAM usage in MB using nvidia-smi.
        Returns 0.0 if NVIDIA GPU is not detected.
        """
        try:
            # Query NVIDIA-SMI for memory usage
            result = await asyncio.to_thread(
                subprocess.run,
                ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Handle multiple GPUs - currently sums them up or takes the first
                lines = result.stdout.strip().splitlines()
                total_used = sum(float(line) for line in lines)
                return total_used
                
        except FileNotFoundError:
            logging.debug("nvidia-smi not found. Cannot read VRAM usage directly.")
        except Exception as e:
            logging.error(f"Error reading VRAM: {e}")
            
        return 0.0

    async def get_loaded_models(self):
        """Ask Ollama which models are currently loaded in memory."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/ps") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('models', [])
        except Exception as e:
            logging.error(f"Could not connect to Ollama at {self.ollama_url}: {e}")
        return []

    async def unload_model(self, model_name: str):
        """Force unload a model by setting keep_alive to 0."""
        if self.dry_run:
            logging.info(f"DRY RUN: Would unload {model_name}")
            return

        logging.info(f"🧹 Unloading model: {model_name}...")
        try:
            async with aiohttp.ClientSession() as session:
                # The 'generate' endpoint with keep_alive=0 forces immediate unload
                payload = {
                    "model": model_name,
                    "keep_alive": 0
                }
                async with session.post(f"{self.ollama_url}/api/generate", json=payload) as resp:
                    if resp.status == 200:
                        logging.info(f"✅ Successfully unloaded {model_name}")
                    else:
                        logging.warning(f"Failed to unload {model_name}. Status: {resp.status}")
        except Exception as e:
            logging.error(f"Error unloading model: {e}")

    async def monitor_loop(self):
        """Main monitoring loop."""
        logging.info(f"🛡️  VRAM Guard Active.")
        logging.info(f"   • Threshold: {self.threshold_mb} MB")
        logging.info(f"   • Check Interval: {self.interval}s")
        logging.info(f"   • Ollama URL: {self.ollama_url}")
        
        while True:
            try:
                vram_used = await self.get_vram_usage()
                
                # If we can't read VRAM (non-Nvidia), we essentially just wait
                if vram_used == 0.0 and self.system != "Darwin": # Darwin (Mac) handling could be added here
                    logging.debug("VRAM reading unavailable or 0.")
                
                elif vram_used > self.threshold_mb:
                    logging.warning(f"⚠️  High VRAM Detected: {vram_used:.0f} MB (Threshold: {self.threshold_mb} MB)")
                    
                    # Get loaded models
                    loaded = await self.get_loaded_models()
                    
                    if loaded:
                        logging.info(f"Found {len(loaded)} loaded models. Initiating cleanup...")
                        for model in loaded:
                            name = model.get('name')
                            # In a more advanced version, you could check 'expires_at' 
                            # or sort by size. For now, we clear to save the system.
                            await self.unload_model(name)
                    else:
                        logging.info("No Ollama models loaded. VRAM usage is from other applications.")
                
                else:
                    logging.debug(f"VRAM OK: {vram_used:.0f} MB")

                await asyncio.sleep(self.interval)
                
            except KeyboardInterrupt:
                logging.info("Stopping VRAM Guard...")
                break
            except Exception as e:
                logging.error(f"Unexpected error in loop: {e}")
                await asyncio.sleep(self.interval)

async def main():
    parser = argparse.ArgumentParser(description="Ollama VRAM Guard & Manager")
    
    parser.add_argument("--threshold", type=int, default=20480, help="VRAM limit in MB before unloading (Default: 20480 for 20GB)")
    parser.add_argument("--interval", type=int, default=5, help="Seconds between checks (Default: 5)")
    parser.add_argument("--host", type=str, default="http://localhost:11434", help="Ollama API URL")
    parser.add_argument("--dry-run", action="store_true", help="Simulate unloading without actually doing it")
    parser.add_argument("--clear-now", action="store_true", help="Immediately unload all models and exit")

    args = parser.parse_args()

    manager = VRAMManager(
        threshold_mb=args.threshold,
        ollama_url=args.host,
        interval=args.interval,
        dry_run=args.dry_run
    )

    if args.clear_now:
        logging.info("🔥 Manual Cleanup Triggered...")
        loaded = await manager.get_loaded_models()
        if loaded:
            for model in loaded:
                await manager.unload_model(model.get('name'))
        else:
            logging.info("No models found to unload.")
        return

    # Start the background monitor
    try:
        await manager.monitor_loop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)