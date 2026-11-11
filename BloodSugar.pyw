import hashlib
import threading
import time
import tkinter as tk
import uuid
import requests
from PIL import Image, ImageDraw, ImageFont

# --- LIBRELINKUP CONFIGURATION ---
EMAIL = "your_follower_email@example.com"
PASSWORD = "your_follower_password"
UNIT = "mmol"  # Use "mmol" (e.g. 5.6) or "mgdl" (e.g. 101)
REGION = "eu"  # "eu" for UK/Europe, "us" for US, etc.
POLL_SECONDS = 60

# --- GOVEE CONFIGURATION ---
GOVEE_API_KEY = "YOUR_GOVEE_API_KEY"
GOVEE_DEVICE_ID = "12:34:56:78:9A:BC:DE:F0"
GOVEE_SKU = "H6076"  # Your floor lamp model number

# --- NEXUS IMAGE OUTPUT PATH ---
NEXUS_IMAGE_PATH = r"C:\LibreNexus\nexus_glucose.png"

# --- BLOOD SUGAR THRESHOLDS (Set to mmol/L by default) ---
# If using mg/dL, change these to e.g. LOW = 70, HIGH = 180, VERY_HIGH = 250
LOW_THRESHOLD = 3.9
HIGH_THRESHOLD = 10.0
VERY_HIGH_THRESHOLD = 13.9
# ----------------------------------------------------------

BASE_HEADERS = {
    "accept-encoding": "gzip",
    "cache-control": "no-cache",
    "connection": "Keep-Alive",
    "content-type": "application/json",
    "product": "llu.android",
    "version": "4.16.0",
}

def rgb_to_int(r, g, b):
    return (r << 16) + (g << 8) + b

# Govee lamp RGB values
GOVEE_COLORS = {
    "LOW": rgb_to_int(255, 0, 0),         # Red
    "IN_RANGE": rgb_to_int(0, 255, 0),    # Green
    "HIGH": rgb_to_int(255, 110, 0),      # Orange
    "VERY_HIGH": rgb_to_int(180, 0, 255), # Purple
}

# Hex colours for the floating desktop widget
WIDGET_HEX_COLORS = {
    "LOW": "#B91414",       # Red
    "IN_RANGE": "#14822D",  # Green
    "HIGH": "#C85500",      # Orange
    "VERY_HIGH": "#7814AF", # Purple
    "LOADING": "#2B2B2B",   # Dark Grey
}

# RGB colours for Nexus PNG image
NEXUS_BG_COLORS = {
    "LOW": (185, 20, 20),
    "IN_RANGE": (20, 130, 45),
    "HIGH": (200, 85, 0),
    "VERY_HIGH": (120, 20, 175),
}

TREND_ARROWS = {
    1: "↓",
    2: "↘",
    3: "→",
    4: "↗",
    5: "↑",
}

def get_range_state(value):
    if value < LOW_THRESHOLD:
        return "LOW"
    elif value <= HIGH_THRESHOLD:
        return "IN_RANGE"
    elif value <= VERY_HIGH_THRESHOLD:
        return "HIGH"
    else:
        return "VERY_HIGH"

def set_govee_color(state):
    url = "https://" + "openapi" + chr(46) + "api" + chr(46) + "govee" + chr(46) + "com/router/api/v1/device/control"
    headers = {
        "Content-Type": "application/json",
        "Govee-API-Key": GOVEE_API_KEY,
    }
    payload = {
        "requestId": str(uuid.uuid4()),
        "payload": {
            "sku": GOVEE_SKU,
            "device": GOVEE_DEVICE_ID,
            "capability": {
                "type": "devices.capabilities.color_setting",
                "instance": "colorRgb",
                "value": GOVEE_COLORS[state],
            },
        },
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp.raise_for_status()

def render_nexus_image(glucose_val, unit_str, trend_code, state):
    img = Image.new("RGB", (640, 48), color=NEXUS_BG_COLORS[state])
    draw = ImageDraw.Draw(img)
    try:
        font_large = ImageFont.truetype("segoeui.ttf", 30)
        font_small = ImageFont.truetype("segoeui.ttf", 18)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    arrow = TREND_ARROWS.get(trend_code, "")
    status_label = state.replace("_", " ")
    draw.text((20, 13), f"BLOOD SUGAR  |  {status_label}", fill=(240, 240, 240), font=font_small)
    draw.text((390, 6), f"{glucose_val} {unit_str}  {arrow}", fill=(255, 255, 255), font=font_large)
    img.save(NEXUS_IMAGE_PATH)

def login(session, base_url):
    resp = session.post(
        f"{base_url}/llu/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=15,
    )
    data = resp.json()

    if isinstance(data.get("data"), dict) and data["data"].get("redirect"):
        new_region = data["data"]["region"]
        base_url = f"https://api-{new_region}.libreview.io"
        resp = session.post(
            f"{base_url}/llu/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
            timeout=15,
        )
        data = resp.json()

    if not isinstance(data.get("data"), dict) or "authTicket" not in data["data"]:
        raise RuntimeError(f"Login failed: {data}")

    token = data["data"]["authTicket"]["token"]
    user_id = data["data"]["user"]["id"]
    account_id = hashlib.sha256(user_id.encode("utf-8")).hexdigest()

    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Account-Id": account_id,
    })
    return base_url

class GlucoseFloatingWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)        # Borderless window
        self.root.attributes("-topmost", True)  # Always on top
        self.root.attributes("-alpha", 0.92)    # Slight transparency

        # Default start position: top-right area of screen
        screen_w = self.root.winfo_screenwidth()
        self.root.geometry(f"+{screen_w - 200}+40")

        self.label = tk.Label(
            self.root,
            text="Loading...",
            font=("Segoe UI", 14, "bold"),
            fg="#FFFFFF",
            bg=WIDGET_HEX_COLORS["LOADING"],
            padx=14,
            pady=6,
        )
        self.label.pack()

        # Enable left-click dragging
        self.label.bind("<ButtonPress-1>", self.start_move)
        self.label.bind("<B1-Motion>", self.do_move)
        # Right-click closes the widget cleanly
        self.label.bind("<Button-3>", lambda e: self.root.destroy())

        self._drag_x = 0
        self._drag_y = 0

    def start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self._drag_x)
        y = self.root.winfo_y() + (event.y - self._drag_y)
        self.root.geometry(f"+{x}+{y}")

    def update_display(self, text, state):
        bg_color = WIDGET_HEX_COLORS.get(state, WIDGET_HEX_COLORS["LOADING"])
        self.root.after(0, lambda: self.label.config(text=text, bg=bg_color))

def poll_loop(widget):
    base_url = f"https://api-{REGION}.libreview.io"
    session = requests.Session()
    session.headers.update(BASE_HEADERS)
    last_state = None

    while True:
        try:
            if "Authorization" not in session.headers:
                base_url = login(session, base_url)

            conn_resp = session.get(f"{base_url}/llu/connections", timeout=15)
            if conn_resp.status_code == 401:
                session.headers.pop("Authorization", None)
                continue

            raw_json = conn_resp.json()
            connections = raw_json.get("data")

            if isinstance(connections, list) and len(connections) > 0:
                patient_id = connections.pop(0)["patientId"]
            elif isinstance(connections, dict) and "patientId" in connections:
                patient_id = connections["patientId"]
            else:
                widget.update_display("No Connection", "LOADING")
                time.sleep(POLL_SECONDS)
                continue

            graph_resp = session.get(f"{base_url}/llu/connections/{patient_id}/graph", timeout=15)
            measurement = graph_resp.json()["data"]["connection"]["glucoseMeasurement"]

            if UNIT.lower() == "mmol":
                value = round(float(measurement["ValueInMgPerDl"]) / 18.0182, 1)
                unit_label = "mmol/L"
            else:
                value = int(measurement["ValueInMgPerDl"])
                unit_label = "mg/dL"

            trend_code = measurement.get("TrendArrow", 3)
            arrow = TREND_ARROWS.get(trend_code, "")
            current_state = get_range_state(value)

            # 1. Update Floating Desktop Pill
            widget.update_display(f"{value} {unit_label} {arrow}", current_state)

            # 2. Save Nexus PNG image
            render_nexus_image(value, unit_label, trend_code, current_state)

            # 3. Update Govee Floor Lamp if range changed
            if current_state != last_state:
                set_govee_color(current_state)
                last_state = current_state

        except Exception:
            widget.update_display("Retrying...", "LOADING")
            session.headers.pop("Authorization", None)

        time.sleep(POLL_SECONDS)

def main():
    widget = GlucoseFloatingWidget()
    worker = threading.Thread(target=poll_loop, args=(widget,), daemon=True)
    worker.start()
    widget.root.mainloop()

if __name__ == "__main__":
    main()
