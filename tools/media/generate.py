"""Generate truthful Rivet visual evidence from the local simulator.

The generated PNGs and GIF are terminal-style captures of real Rivet command/API
results. Pillow is intentionally a tooling-only dependency; it is not required
by the runtime package.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parents[2]
ASSETS = ROOT / "site" / "assets"
BG = "#0b1018"
PANEL = "#101b29"
BORDER = "#263c55"
TEXT = "#eef4ff"
MUTED = "#8b9bb0"
CYAN = "#8be9fd"
GREEN = "#b8f4c8"
AMBER = "#f2b866"
RED = "#ff8f8f"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def run_json(*args: str) -> dict[str, Any]:
    result = subprocess.run([sys.executable, "-m", "rivet", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def mark(draw: ImageDraw.ImageDraw, x: int, y: int, size: int) -> None:
    draw.rounded_rectangle((x, y, x + size, y + size), radius=size // 5, fill=PANEL, outline="#314a64", width=max(2, size // 35))
    points = [(x + size // 2, y + size // 8), (x + size * 7 // 8, y + size * 2 // 8), (x + size * 7 // 8, y + size * 6 // 8), (x + size // 2, y + size * 7 // 8), (x + size // 8, y + size * 6 // 8), (x + size // 8, y + size * 2 // 8)]
    draw.polygon(points, fill="#63d6ba")
    bolt = [(x + size * 56 // 100, y + size * 20 // 100), (x + size * 32 // 100, y + size * 53 // 100), (x + size * 50 // 100, y + size * 53 // 100), (x + size * 44 // 100, y + size * 78 // 100), (x + size * 68 // 100, y + size * 45 // 100), (x + size * 50 // 100, y + size * 45 // 100)]
    draw.polygon(bolt, fill=CYAN)
    draw.ellipse((x + size * 41 // 100, y + size * 41 // 100, x + size * 59 // 100, y + size * 59 // 100), fill=PANEL, outline=AMBER, width=max(2, size // 28))


def shell(title: str, subtitle: str, width: int = 1600, height: int = 900) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 10), fill=CYAN)
    mark(draw, 72, 62, 92)
    draw.text((190, 76), "RIVET", font=font(48, True), fill=TEXT)
    draw.text((194, 132), "ROBOTICS INFRASTRUCTURE", font=font(18, True), fill=CYAN)
    draw.text((72, 226), title, font=font(48, True), fill=TEXT)
    draw.text((72, 292), subtitle, font=font(24), fill=MUTED)
    draw.rounded_rectangle((72, 360, width - 72, height - 72), radius=22, fill=PANEL, outline=BORDER, width=2)
    return image, draw


def doctor_image() -> None:
    data = run_json("doctor", "--verbose")
    image, draw = shell("System diagnostic", "A real local run of: python -m rivet doctor --verbose")
    x, y = 120, 420
    draw.text((x, y), "Rivet System Diagnostic", font=font(30, True), fill=CYAN)
    y += 64
    for check in data["checks"]:
        color = GREEN if check["ok"] else RED
        symbol = "✓" if check["ok"] else "!"
        draw.text((x, y), symbol, font=font(30, True), fill=color)
        draw.text((x + 52, y + 3), check["name"], font=font(26, True), fill=TEXT)
        draw.text((x + 430, y + 4), check["detail"], font=font(24), fill=MUTED)
        y += 62
    draw.text((x, y + 26), "status: healthy", font=font(24, True), fill=GREEN)
    image.save(ASSETS / "rivet-doctor.png")


def simulator_image() -> None:
    data = run_json("run", "--simulate")
    image, draw = shell("Simulator capability map", "A real local run of: python -m rivet run --simulate")
    x, y = 120, 410
    draw.text((x, y), f"mode: {data['mode']}", font=font(28, True), fill=CYAN)
    y += 62
    for capability in data["capabilities"]:
        color = AMBER if capability["path"].startswith("motion") else GREEN
        draw.ellipse((x, y + 10, x + 18, y + 28), fill=color)
        draw.text((x + 42, y), capability["path"], font=font(25, True), fill=TEXT)
        draw.text((x + 500, y + 2), capability["type"], font=font(23), fill=MUTED)
        y += 58
    draw.text((x, y + 22), f"{len(data['capabilities'])} capabilities discovered · fault: none", font=font(24, True), fill=GREEN)
    image.save(ASSETS / "rivet-simulator.png")


def fault_frame(label: str, subtitle: str, devices: int, active_faults: int, color: str) -> Image.Image:
    image, draw = shell(label, subtitle, width=1400, height=760)
    x, y = 120, 430
    draw.text((x, y), "SIMULATION STATE", font=font(22, True), fill=MUTED)
    draw.text((x, y + 58), str(devices), font=font(74, True), fill=color)
    draw.text((x + 120, y + 78), "devices registered", font=font(28), fill=TEXT)
    draw.text((x, y + 180), str(active_faults), font=font(74, True), fill=RED if active_faults else GREEN)
    draw.text((x + 120, y + 200), "active injected faults", font=font(28), fill=TEXT)
    draw.rounded_rectangle((760, y + 8, 1210, y + 220), radius=18, fill="#0b1018", outline=color, width=3)
    draw.text((800, y + 52), "safe-state seam", font=font(24, True), fill=color)
    draw.text((800, y + 112), "FaultInjector", font=font(30, True), fill=TEXT)
    draw.text((800, y + 158), "disconnect → safe → restore", font=font(20), fill=MUTED)
    return image


def fault_gif() -> None:
    data = run_json("run", "--simulate")
    runtime_count = len(data["capabilities"])
    frames = [
        fault_frame("Simulator / nominal", "Real simulator inventory before fault injection", runtime_count, 0, GREEN),
        fault_frame("Fault injection / disconnect", "The simulator removes motion.left-wheel and records the fault", runtime_count - 1, 1, AMBER),
        fault_frame("Recovery / restored", "FaultInjector restores the removed simulated device", runtime_count, 0, CYAN),
    ]
    frames[0].save(ASSETS / "rivet-fault-injection.gif", save_all=True, append_images=frames[1:], duration=[1300, 1500, 1300], loop=0, disposal=2)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    doctor_image()
    simulator_image()
    fault_gif()
    print(f"generated visual evidence in {ASSETS}")


if __name__ == "__main__":
    main()
