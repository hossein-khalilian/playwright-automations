import argparse
import os
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from dotenv import load_dotenv
from playwright.sync_api import BrowserContext, Page, sync_playwright

from automation.utils.config import config
from automation.utils.system_resolution import get_system_resolution

# Base directory for automation backend
BASE_DIR = Path(__file__).resolve().parent.parent

# Path to store browser context (persistent profile)
CONTEXT_PATH = BASE_DIR / "browser_profiles" / "default"


def generate_random_name() -> Tuple[str, str]:
    """Generate random first and last name."""
    first_names = [
        "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery",
        "Cameron", "Dakota", "Quinn", "Blake", "Sage", "River", "Phoenix"
    ]
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson"
    ]
    return random.choice(first_names), random.choice(last_names)


def generate_username(first_name: str, last_name: str) -> str:
    """Generate a username based on first and last name."""
    base = f"{first_name.lower()}{last_name.lower()}"
    # Add random numbers to increase uniqueness
    random_suffix = random.randint(100, 999)
    return f"{base}{random_suffix}"


def generate_birthday() -> Tuple[int, int, int]:
    """Generate a random birthday (day, month, year)."""
    # Generate a year between 18-65 years ago (reasonable age range)
    current_year = datetime.now().year
    birth_year = random.randint(current_year - 65, current_year - 18)
    birth_month = random.randint(1, 12)
    # Handle different month lengths
    if birth_month in [1, 3, 5, 7, 8, 10, 12]:
        max_day = 31
    elif birth_month in [4, 6, 9, 11]:
        max_day = 30
    else:  # February
        # Simple leap year check
        if birth_year % 4 == 0 and (birth_year % 100 != 0 or birth_year % 400 == 0):
            max_day = 29
        else:
            max_day = 28
    birth_day = random.randint(1, max_day)
    return birth_day, birth_month, birth_year


def save_to_mongodb(account_data: Dict) -> bool:
    """Save account information to MongoDB collection."""
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, DuplicateKeyError

        mongo_uri = config.get("mongo_uri")
        db_name = config.get("mongo_db_name")
        collection_name = config.get("mongo_account_collection")

        if not mongo_uri:
            print("[!] Warning: MONGO_URI not set. Account will not be saved to database.")
            return False

        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        collection = db[collection_name]

        # Add timestamp
        account_data["created_at"] = datetime.utcnow()
        account_data["status"] = "active"

        # Try to insert, handle duplicates
        try:
            result = collection.insert_one(account_data)
            print(f"[+] Account saved to MongoDB with ID: {result.inserted_id}")
            client.close()
            return True
        except DuplicateKeyError:
            print("[!] Account with this email already exists in database.")
            client.close()
            return False

    except ConnectionFailure:
        print("[!] Error: Could not connect to MongoDB. Account will not be saved.")
        return False
    except ImportError:
        print("[!] Error: pymongo not installed. Install it with: pip install pymongo")
        return False
    except Exception as e:
        print(f"[!] Error saving to MongoDB: {e}")
        return False


def setup_stealth_mode(context: BrowserContext, page: Page) -> None:
    """
    Inject comprehensive stealth scripts using CDP to make the browser appear as a real user browser.
    This helps bypass Google's automation detection.
    """
    stealth_script = """
    (function() {
        'use strict';
        
        // Remove webdriver property completely - this is the most important
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Delete webdriver from prototype chain
        try {
            delete navigator.__proto__.webdriver;
        } catch(e) {}

        // Override plugins to look real
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const plugins = [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
                ];
                plugins.item = function(index) { return this[index] || null; };
                plugins.namedItem = function(name) { 
                    for (let i = 0; i < this.length; i++) {
                        if (this[i].name === name) return this[i];
                    }
                    return null;
                };
                return plugins;
            }
        });

        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });

        // Override permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => {
            if (parameters.name === 'notifications') {
                return Promise.resolve({ state: Notification.permission });
            }
            return originalQuery(parameters);
        };

        // Full Chrome object - Google checks for this
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {
                isInstalled: false,
                InstallState: {
                    DISABLED: "disabled",
                    INSTALLED: "installed",
                    NOT_INSTALLED: "not_installed"
                },
                RunningState: {
                    CANNOT_RUN: "cannot_run",
                    READY_TO_RUN: "ready_to_run",
                    RUNNING: "running"
                }
            }
        };

        // Override WebGL vendor/renderer
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.call(this, parameter);
        };
    })();
    """

    # Inject via CDP which runs before page scripts - this is critical
    try:
        cdp_session = context.new_cdp_session(page)
        cdp_session.send(
            "Page.addScriptToEvaluateOnNewDocument", {"source": stealth_script}
        )
    except Exception as e:
        print(f"[!] Warning: Could not set up CDP stealth: {e}")

    # Also add via context init script for additional coverage
    context.add_init_script(stealth_script)


def create_google_account(
    page: Page,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    phone_number: Optional[str] = None,
    birthday_day: Optional[int] = None,
    birthday_month: Optional[int] = None,
    birthday_year: Optional[int] = None,
    gender: Optional[str] = None,
) -> Optional[Dict]:
    """
    Create a Google account using the provided information.
    
    Returns a dictionary with account information if successful, None otherwise.
    """
    try:
        # Generate random names if not provided
        if not first_name or not last_name:
            first_name, last_name = generate_random_name()
            print(f"[*] Generated random name: {first_name} {last_name}")

        # Generate username if not provided
        if not username:
            username = generate_username(first_name, last_name)
            print(f"[*] Generated username: {username}")

        # Generate password if not provided
        if not password:
            # Generate a strong password
            import string
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(random.choice(chars) for _ in range(16))
            print(f"[*] Generated password: {'*' * 16}")

        # Generate birthday if not provided
        if not birthday_day or not birthday_month or not birthday_year:
            birthday_day, birthday_month, birthday_year = generate_birthday()
            print(f"[*] Generated birthday: {birthday_day}/{birthday_month}/{birthday_year}")

        # Generate gender if not provided
        if not gender:
            gender = random.choice(["Male", "Female", "Rather not say"])
            print(f"[*] Generated gender: {gender}")

        # Map month number to month name
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        month_name = month_names[birthday_month - 1]

        print("\n[*] Starting Google account creation flow...")
        
        # Step 1: Go to Google.com
        print("[*] Navigating to Google.com...")
        page.goto("https://www.google.com/", wait_until="domcontentloaded", timeout=60_000)
        time.sleep(random.uniform(1.0, 2.0))

        # Step 2: Click Sign in
        print("[*] Clicking Sign in...")
        page.get_by_role("link", name="Sign in").click()
        time.sleep(random.uniform(2.0, 3.0))

        # Step 3: Click Create account
        print("[*] Clicking Create account...")
        page.get_by_role("button", name="Create account").click()
        time.sleep(random.uniform(1.0, 2.0))

        # Step 4: Click "For my personal use"
        print("[*] Selecting 'For my personal use'...")
        page.get_by_text("For my personal use").click()
        time.sleep(random.uniform(1.5, 2.5))

        # Step 5: First Name
        print(f"[*] Entering first name: {first_name}...")
        first_name_input = page.get_by_role("textbox", name="First name")
        first_name_input.wait_for(timeout=15_000)
        first_name_input.click()
        time.sleep(random.uniform(0.3, 0.7))
        first_name_input.fill(first_name)
        time.sleep(random.uniform(0.3, 0.7))
        first_name_input.press("Tab")
        time.sleep(random.uniform(0.5, 1.0))

        # Step 6: Last Name
        print(f"[*] Entering last name: {last_name}...")
        last_name_input = page.get_by_role("textbox", name="Last name (optional)")
        last_name_input.fill(last_name)
        time.sleep(random.uniform(0.5, 1.0))

        # Step 7: Click Next
        print("[*] Clicking Next...")
        page.get_by_role("button", name="Next").click()
        time.sleep(random.uniform(2.0, 3.5))

        # Step 8: Birthday and Gender
        print("[*] Entering birthday and gender...")
        
        # Select month
        print(f"[*] Selecting month: {month_name}...")
        month_dropdown = page.locator(".VfPpkd-aPP78e").first
        month_dropdown.wait_for(timeout=10_000)
        month_dropdown.click()
        time.sleep(random.uniform(0.5, 1.0))
        page.get_by_role("option", name=month_name).click()
        time.sleep(random.uniform(0.5, 1.0))

        # Enter day
        print(f"[*] Entering day: {birthday_day}...")
        day_input = page.get_by_role("textbox", name="Day")
        day_input.click()
        time.sleep(random.uniform(0.3, 0.7))
        day_input.fill(str(birthday_day))
        time.sleep(random.uniform(0.5, 1.0))

        # Enter year
        print(f"[*] Entering year: {birthday_year}...")
        year_input = page.get_by_role("textbox", name="Year")
        year_input.click()
        time.sleep(random.uniform(0.3, 0.7))
        year_input.fill(str(birthday_year))
        time.sleep(random.uniform(0.5, 1.0))

        # Select gender
        print(f"[*] Selecting gender: {gender}...")
        gender_dropdown = page.locator("#gender > .VfPpkd-O1htCb > .VfPpkd-TkwUic > .VfPpkd-aPP78e")
        gender_dropdown.click()
        time.sleep(random.uniform(0.5, 1.0))
        page.get_by_role("option", name=gender, exact=True).click()
        time.sleep(random.uniform(0.5, 1.0))

        # Click Next
        print("[*] Clicking Next for birthday/gender...")
        page.get_by_role("button", name="Next").click()
        time.sleep(random.uniform(2.0, 3.5))

        # Step 9: Username
        print(f"[*] Entering username: {username}...")
        username_input = page.get_by_role("textbox", name="Username")
        username_input.wait_for(timeout=15_000)
        username_input.click()
        time.sleep(random.uniform(0.3, 0.7))
        username_input.fill(username)
        time.sleep(random.uniform(1.0, 2.0))

        # Click Next
        print("[*] Clicking Next for username...")
        page.get_by_role("button", name="Next").click()
        time.sleep(random.uniform(2.0, 3.5))

        # Step 10: Handle username availability
        # Check if username is taken and handle suggested alternatives
        try:
            # Wait a bit to see if we get redirected or if there are suggestions
            time.sleep(random.uniform(2.0, 3.0))
            
            # Check if we're still on username page (username taken)
            current_url = page.url
            username_input_check = page.get_by_role("textbox", name="Username")
            
            # Check if username field is still visible (means username was rejected)
            try:
                username_input_check.wait_for(timeout=3_000, state="visible")
                # Username was likely rejected, look for suggested usernames
                print("[*] Username may be taken, looking for suggestions...")
                
                # Try to find suggested username buttons (they appear as buttons with username-like text)
                # Look for buttons that contain alphanumeric text (likely suggested usernames)
                all_buttons = page.locator("button")
                button_count = all_buttons.count()
                
                # Try clicking on a suggested username button if available
                found_suggestion = False
                for i in range(min(button_count, 10)):  # Check first 10 buttons
                    try:
                        button = all_buttons.nth(i)
                        button_text = button.inner_text()
                        # Suggested usernames are usually alphanumeric and don't say "Next" or "Skip"
                        if button_text and len(button_text) > 3 and button_text.isalnum() and \
                           button_text.lower() not in ["next", "skip", "back", "cancel"]:
                            print(f"[*] Found suggested username: {button_text}, clicking...")
                            button.click()
                            time.sleep(random.uniform(1.0, 2.0))
                            # Update username to the selected one
                            username = button_text
                            found_suggestion = True
                            break
                    except Exception:
                        continue
                
                if not found_suggestion:
                    # If no suggestions found, try generating a new username
                    print(f"[!] Username {username} is not available. Generating new username...")
                    username = generate_username(first_name, last_name)
                    username_input_check.click()
                    time.sleep(random.uniform(0.3, 0.7))
                    username_input_check.fill(username)
                    time.sleep(random.uniform(1.0, 2.0))
                    page.get_by_role("button", name="Next").click()
                    time.sleep(random.uniform(2.0, 3.5))
                else:
                    # Click Next after selecting suggested username
                    page.get_by_role("button", name="Next").click()
                    time.sleep(random.uniform(2.0, 3.5))
            except Exception:
                # Username field not visible, username was accepted
                pass
        except Exception as e:
            print(f"[*] Username handling: {e}")
            pass  # Username was accepted, continue

        # Step 11: Password
        print("[*] Entering password...")
        password_input = page.get_by_role("textbox", name="Password")
        password_input.wait_for(timeout=15_000)
        password_input.fill(password)
        time.sleep(random.uniform(0.3, 0.7))
        password_input.press("Tab")
        time.sleep(random.uniform(0.5, 1.0))

        # Step 12: Confirm Password
        print("[*] Confirming password...")
        confirm_password_input = page.get_by_role("textbox", name="Confirm")
        confirm_password_input.fill(password)
        time.sleep(random.uniform(0.5, 1.0))

        # Step 13: Click Next
        print("[*] Clicking Next for password...")
        page.get_by_role("button", name="Next").click()
        time.sleep(random.uniform(2.0, 3.5))

        # Step 14: Phone Verification (if required)
        print("[*] Checking for phone verification requirement...")
        try:
            phone_input = page.get_by_role("textbox", name=re.compile("phone|Phone", re.IGNORECASE)).or_(
                page.locator('input[type="tel"]')
            )
            phone_input.wait_for(timeout=5_000)
            if phone_number:
                print(f"[*] Entering phone number: {phone_number}")
                phone_input.click()
                time.sleep(random.uniform(0.3, 0.7))
                phone_input.fill(phone_number)
                time.sleep(random.uniform(1.0, 2.0))

                page.get_by_role("button", name="Next").click()
                time.sleep(random.uniform(2.0, 3.5))

                # Wait for verification code input
                print("[!] Phone verification required. Please enter the verification code manually.")
                code_input = page.get_by_role("textbox", name=re.compile("code|Code|verification", re.IGNORECASE)).or_(
                    page.locator('input[type="tel"]')
                )
                code_input.wait_for(timeout=60_000)
                input("    Enter the verification code in the browser and press Enter here to continue...")
                time.sleep(random.uniform(1.0, 2.0))

                # Click Verify or Next
                try:
                    page.get_by_role("button", name="Verify").click()
                except Exception:
                    page.get_by_role("button", name="Next").click()
                time.sleep(random.uniform(2.0, 3.5))
            else:
                print("[!] Phone verification required but no phone number provided.")
                print("[!] Please complete the verification manually in the browser.")
                input("    After completing verification, press Enter here to continue...")
        except Exception:
            print("[*] Phone verification not required or skipped.")

        # Step 15: Recovery Email (optional, may be skipped)
        print("[*] Checking for recovery email...")
        try:
            recovery_email_input = page.locator('input[type="email"]')
            recovery_email_input.wait_for(timeout=3_000)
            print("[*] Skipping recovery email (optional)...")
            skip_button = page.locator('button:has-text("Skip")').or_(page.locator('button:has-text("Next")'))
            skip_button.first.click()
            time.sleep(random.uniform(2.0, 3.0))
        except Exception:
            pass  # Recovery email step not present

        # Step 16: Terms and Conditions
        print("[*] Accepting terms and conditions...")
        try:
            # Scroll to find the terms checkbox
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(random.uniform(1.0, 2.0))

            # Look for terms acceptance
            terms_checkbox = page.locator('input[type="checkbox"]').or_(page.locator('div[role="checkbox"]'))
            terms_checkbox.first.wait_for(timeout=5_000)
            terms_checkbox.first.click()
            time.sleep(random.uniform(0.5, 1.0))

            # Click Create Account or I Agree
            create_button = page.locator('button:has-text("Create account")').or_(
                page.locator('button:has-text("I agree")')
            )
            create_button.first.click()
            time.sleep(random.uniform(3.0, 5.0))
        except Exception as e:
            print(f"[!] Could not find terms checkbox automatically: {e}")
            print("[!] Please accept terms manually in the browser.")
            input("    After accepting terms, press Enter here to continue...")

        # Wait for account creation to complete
        print("[*] Waiting for account creation to complete...")
        page.wait_for_load_state("networkidle", timeout=60_000)
        time.sleep(random.uniform(2.0, 3.0))

        # Check if we're on a success page or logged in
        current_url = page.url
        if "accounts.google.com" in current_url or "myaccount.google.com" in current_url:
            email = f"{username}@gmail.com"
            print(f"\n[+] Successfully created Google account!")
            print(f"[+] Email: {email}")
            print(f"[+] Password: {'*' * len(password)}")

            account_data = {
                "email": email,
                "username": username,
                "password": password,  # In production, consider encrypting this
                "first_name": first_name,
                "last_name": last_name,
                "birthday_day": birthday_day,
                "birthday_month": birthday_month,
                "birthday_year": birthday_year,
                "gender": gender,
                "phone_number": phone_number,
                "created_at": datetime.utcnow().isoformat(),
            }

            return account_data
        else:
            print(f"\n[!] Account creation may not have completed. Current URL: {current_url}")
            print("[!] Please verify manually in the browser.")
            return None

    except Exception as exc:
        print(f"\n[-] Error during Google account creation: {exc}")
        import traceback
        traceback.print_exc()
        return None


def run_account_creation(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    phone_number: Optional[str] = None,
    birthday_day: Optional[int] = None,
    birthday_month: Optional[int] = None,
    birthday_year: Optional[int] = None,
    gender: Optional[str] = None,
    headless: bool = False,
    profile_name: str = "default",
) -> None:
    """
    Create a Google account and save it to MongoDB if successful.
    """
    # Use a separate profile for account creation to avoid conflicts
    context_path = BASE_DIR / "browser_profiles" / f"{profile_name}_creation"
    
    print(f"[*] Using browser profile at: {context_path}")

    with sync_playwright() as p:
        # Use a realistic Chrome user agent
        user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )

        # Get system resolution for viewport
        viewport = get_system_resolution()

        context = p.chromium.launch_persistent_context(
            user_data_dir=str(context_path),
            headless=headless,
            viewport=viewport,
            user_agent=user_agent,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--exclude-switches=enable-automation",
                "--start-maximized",
            ],
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
            },
        )

        page = context.pages[0] if context.pages else context.new_page()

        # Navigate to a neutral page first
        print("[*] Establishing browser session...")
        page.goto(
            "https://www.google.com", wait_until="domcontentloaded", timeout=10000
        )
        time.sleep(random.uniform(1.0, 2.0))

        # Apply comprehensive stealth mode
        setup_stealth_mode(context, page)
        time.sleep(0.5)

        try:
            # Create the account
            account_data = create_google_account(
                page,
                first_name=first_name,
                last_name=last_name,
                username=username,
                password=password,
                phone_number=phone_number,
                birthday_day=birthday_day,
                birthday_month=birthday_month,
                birthday_year=birthday_year,
                gender=gender,
            )

            if account_data:
                # Save to MongoDB
                print("\n[*] Saving account to MongoDB...")
                saved = save_to_mongodb(account_data)
                if saved:
                    print("[+] Account information saved to MongoDB successfully!")
                else:
                    print("[!] Account created but not saved to MongoDB.")
                    print("[!] Account details:")
                    for key, value in account_data.items():
                        if key != "password":
                            print(f"    {key}: {value}")
                        else:
                            print(f"    {key}: {'*' * len(value)}")
            else:
                print("\n[-] Account creation failed or was not completed.")

        finally:
            print("[*] Closing browser context...")
            # Keep browser open for a bit to allow manual verification if needed
            if not headless:
                input("\n[*] Press Enter to close the browser...")
            context.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a Google account and save it to MongoDB."
    )
    parser.add_argument(
        "--first-name",
        dest="first_name",
        type=str,
        help="First name for the account (random if not provided)",
    )
    parser.add_argument(
        "--last-name",
        dest="last_name",
        type=str,
        help="Last name for the account (random if not provided)",
    )
    parser.add_argument(
        "--username",
        dest="username",
        type=str,
        help="Username for the account (random if not provided)",
    )
    parser.add_argument(
        "--password",
        dest="password",
        type=str,
        help="Password for the account (random if not provided)",
    )
    parser.add_argument(
        "--phone",
        dest="phone_number",
        type=str,
        help="Phone number for verification (required if Google asks for it)",
    )
    parser.add_argument(
        "--birthday-day",
        dest="birthday_day",
        type=int,
        help="Birthday day (1-31, random if not provided)",
    )
    parser.add_argument(
        "--birthday-month",
        dest="birthday_month",
        type=int,
        help="Birthday month (1-12, random if not provided)",
    )
    parser.add_argument(
        "--birthday-year",
        dest="birthday_year",
        type=int,
        help="Birthday year (random if not provided)",
    )
    parser.add_argument(
        "--gender",
        dest="gender",
        type=str,
        choices=["Male", "Female", "Rather not say"],
        help="Gender (random if not provided)",
    )
    parser.add_argument(
        "--headless",
        dest="headless",
        action="store_true",
        help="Run the browser in headless mode (not recommended for account creation)",
    )
    parser.add_argument(
        "--profile",
        dest="profile_name",
        type=str,
        default="default",
        help="Browser profile name to use (default: default)",
    )

    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()

    run_account_creation(
        first_name=args.first_name,
        last_name=args.last_name,
        username=args.username,
        password=args.password,
        phone_number=args.phone_number,
        birthday_day=args.birthday_day,
        birthday_month=args.birthday_month,
        birthday_year=args.birthday_year,
        gender=args.gender,
        headless=args.headless,
        profile_name=args.profile_name,
    )


if __name__ == "__main__":
    main()

