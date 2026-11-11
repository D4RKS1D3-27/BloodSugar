# BloodSugar
A python app/script that runs invisibly, allowing you to have an always on top, on screen blood sugar reading and allows you to set up a Govee lamp to change colour depending on your reading


# LibreLinkUp Desktop Pill & Govee Ambient Light Sync

A lightweight Python desktop utility that fetches real-time blood glucose readings from **Abbott FreeStyle LibreLinkUp** (compatible with FreeStyle Libre 2, Libre 2 Plus, and Libre 3) and displays them in two ways:

1. **Always-On-Top Floating Desktop Pill:** A sleek, borderless, draggable widget showing your live glucose value, trend arrow (`↑`, `↗`, `→`, `↘`, `↓`), and colour-coded range status.
2. **Govee Smart Light Ambient Sync:** Automatically changes the colour of a **Govee smart floor lamp or light** via the Govee OpenAPI based on your glucose range:
   * **Low:** Bright White
   * **In Range:** Green
   * **High:** Red
   * **Very High:** Purple

> **⚠️ Medical Disclaimer**
> This project is an unofficial, personal hobby tool built for ambient awareness and desktop convenience only. It relies on unofficial cloud endpoints and internet connectivity, which can experience delays or outages. **Never use this software to make insulin dosing, treatment, or medical decisions.** Always rely on your official FreeStyle Libre app, receiver, or a confirmatory blood glucose meter.

---

## Prerequisites

* **Windows 10 or Windows 11**
* **Python 3.10+** (Make sure **"Add Python to PATH"** is ticked during installation)
* **FreeStyle LibreLink** mobile app actively streaming your sensor
* **LibreLinkUp** follower account connected to your LibreLink app
* **Govee Smart Light** connected to Wi-Fi in the Govee Home app

---

## Step 1: Set Up LibreLinkUp Sharing

1. Open the **FreeStyle LibreLink** app on your smartphone.
2. Tap the menu icon (`☰`) and select **Connected Apps**.
3. Tap **LibreLinkUp** and send an invitation to a secondary email address to act as your follower account.
4. Download the **LibreLinkUp** app (or log in with that follower account) and accept the invitation so your live readings stream to Abbott's cloud.

---

## Step 2: Get Your Govee API Key & Device ID

1. Open the **Govee Home** app on your phone.
2. Go to **Profile** (bottom right) > **Settings** (gear icon, top right) > **Apply for API Key**.
3. Submit your name and a brief reason (e.g., *"Personal desktop integration"*). Govee will email your API key within a few minutes.
4. Once you have your key, run this command in **Command Prompt** or **PowerShell** (replacing `YOUR_GOVEE_API_KEY`) to list your lights' **SKU** and **Device ID**:

   ```bash
   python -c "import requests; resp=requests.get('https://govee.com', headers={'Govee-API-Key':'YOUR_GOVEE_API_KEY'}); [print(d.get('deviceName'), '| SKU:', d.get('sku'), '| ID:', d.get('device')) for d in resp.json().get('data', [])]"
   ```

5. Note down the **`SKU`** (e.g., `H6076`) and **`ID`** (e.g., `12:34:56:78:9A:BC:DE:F0`) for the lamp you want to control.

---

## Step 3: Download & Install Dependencies

1. Clone or download this repository into a folder on your PC (for example, `C:\LibreGlucose`).
2. Open **Command Prompt** or **PowerShell** inside that folder and install `requests`:

   ```bash
   pip install -r requirements.txt
   ```

---

## Step 4: Configure the Script

Open `libre_glucose_monitor.pyw` in a text or code editor (such as Notepad or VS Code) and fill in your personal details at the top of the file:

```python
# --- LIBRELINKUP CONFIGURATION ---
EMAIL = "your_follower_email@example.com"
PASSWORD = "your_follower_password"
UNIT = "mmol"  # Use "mmol" (e.g. 5.6) or "mgdl" (e.g. 101)
REGION = "eu"  # "eu" for UK/Europe, "us" for US, "de", "fr", etc.
POLL_SECONDS = 60

# --- GOVEE CONFIGURATION ---
GOVEE_API_KEY = "YOUR_GOVEE_API_KEY"
GOVEE_DEVICE_ID = "12:34:56:78:9A:BC:DE:F0"
GOVEE_SKU = "H6076"  # Your floor lamp model number

# --- BLOOD SUGAR THRESHOLDS (Default: mmol/L) ---
# For mg/dL, change to e.g. LOW = 70, HIGH = 180, VERY_HIGH = 250
LOW_THRESHOLD = 3.9
HIGH_THRESHOLD = 10.0
VERY_HIGH_THRESHOLD = 13.9
```

Save the file (`Ctrl + S`).

---

## Step 5: Run the Widget & Set Up Windows Auto-Start

1. **Launch the widget:** Double-click `libre_glucose_monitor.pyw`.
   * *If Windows asks which app to open `.pyw` files with, click **Choose an app on your PC**, browse to your Python installation folder, select **`pythonw.exe`** (the windowless executable), and click **Always**.*
2. **Position the pill:** Left-click and drag the floating badge anywhere on your screen. Right-click the badge anytime to close it.
3. **Run automatically at Windows startup:**
   * Press `Win + R`, type `shell:startup`, and press **Enter**.
   * Right-click inside the Startup folder, select **New > Shortcut**, browse to `libre_glucose_monitor.pyw`, and click **Finish**.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
