import csv
import os
import time
from DrissionPage import ChromiumPage
from concurrent.futures import ThreadPoolExecutor

# --- Configuration ---
CSV_FILE = 'file.csv'
TARGET_URL = 'https://couriers.indrive.com/register'
MAX_WORKERS = 3 
# ---------------------

# Country Code Map
COUNTRY_MAP = {
    "255": "Tanzania",
    "95": "Myanmar",
    "51": "Peru",
    "1": "United States",
    "44": "United Kingdom"
}

# 1. Create dummy file if missing
if not os.path.exists(CSV_FILE):
    print(f"Creating sample '{CSV_FILE}'...")
    data = [
        ["Range", "Prefix", "Number", "My Payterm", "My Payout", "Limits"],
        ["Tanzania LX 30D", "", "255679155400", "Monthly60", "$ 100", "SD : 30 | SW : 0"],
        ["Myanmar LX 03F", "", "959894160433", "Monthly60", "$ 100", "SD : 30 | SW : 0"]
    ]
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerows(data)

def get_country_name(number):
    for code in sorted(COUNTRY_MAP.keys(), key=len, reverse=True):
        if number.startswith(code):
            return COUNTRY_MAP[code], code
    return None, None

def process_number(row, browser):
    raw_number = row.get('Number', '').strip()
    range_name = row.get('Range', 'Unknown')
    status = "Unknown"

    if not raw_number:
        return

    tab = browser.new_tab(TARGET_URL)
    
    try:
        # --- Step A: Detect Country ---
        country_name, country_code = get_country_name(raw_number)
        
        if not country_name:
            status = "❌ ERROR (Unknown Country Code)"
            raise Exception("Unknown country code")

        # --- Step B: Open Dropdown ---
        country_btn = tab.ele('@aria-label=Select a country code', timeout=5)
        country_btn.click()
        time.sleep(0.5)

        # --- Step C: Type to Filter (Optional but helps) ---
        # We type just in case the list is long, to scroll to the right item
        tab.actions.type(country_name)
        time.sleep(0.5)

        # --- Step D: CLICK THE COUNTRY TEXT DIRECTLY ---
        # This is the fix: Find the text "Tanzania" or "Myanmar" and click it.
        # This forces the selection and closes the dropdown.
        country_option = tab.ele(f'text:{country_name}', timeout=3)
        country_option.click()
        time.sleep(0.5) # Wait for dropdown to close

        # --- Step E: Input Number ---
        input_box = tab.ele('@data-testid=phone-number-form-input-phone-input', timeout=5)
        
        # Wait for mask to update
        expected_placeholder_part = f"+{country_code}"
        for _ in range(10):
            val = input_box.attr('placeholder') or ""
            if expected_placeholder_part in val: break
            time.sleep(0.2)

        # Calculate local number (remove country code)
        local_number = raw_number[len(country_code):]
        
        # Clear and Type
        input_box.clear()
        time.sleep(0.2)
        input_box.input(local_number)
        time.sleep(0.3)

        # --- Step F: Click Next ---
        next_btn = tab.ele('@data-testid=phone-number-form-next-button', timeout=3)
        next_btn.click()

        # --- Step G: Status Detection ---
        time.sleep(3)

        if tab.ele('text:Resend', timeout=0.5):
            status = "✅ SUCCESS (SMS Sent)"
        elif tab.ele('text:code', timeout=0.5):
             status = "✅ SUCCESS (Code Screen)"
        elif not tab.ele('@data-testid=phone-number-form-next-button', timeout=0.5):
             status = "✅ SUCCESS (Form Moved)"
        elif tab.ele('@aria-invalid=true', timeout=0.5):
             status = "❌ FAILED (Invalid Format)"
        else:
             status = "⚠️ NO RESPONSE"

    except Exception as e:
        status = f"❌ ERROR ({e})"
    finally:
        print(f"[{range_name}] {raw_number} -> {status}")
        tab.close()

if __name__ == '__main__':
    browser = ChromiumPage()
    
    rows = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} numbers.\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for row in rows:
            executor.submit(process_number, row, browser)
            
    print("\nDone.")
    input("Press Enter to exit...")
    browser.quit()