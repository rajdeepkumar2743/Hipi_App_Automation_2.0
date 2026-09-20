# HiPi Automation 2.0

This project is a mobile automation framework for the HiPi Android application, built with Python, PyTest, Appium, and the Page Object Model (POM). It covers login flows, feed interactions, video controls, and social actions on the app UI.

## Overview

The suite validates real user workflows against the HiPi app by automating Android device interactions through Appium. The project is organized around reusable page objects, device/environment configuration, and pytest fixtures that handle driver creation, login reuse, Appium recovery, and failure capture.

Key goals of the framework:

- Automate critical user journeys in the HiPi app
- Keep test logic independent from UI locators
- Reuse Appium sessions efficiently for smoke and feed tests
- Support Android emulator and real-device execution
- Produce Allure and HTML reporting
- Recover from transient Appium/UiAutomator2 issues automatically

---

## Tech Stack

- Python 3
- PyTest
- Appium Python Client
- Selenium WebDriver
- Allure Reports
- Android / Appium UiAutomator2
- dotenv for environment variable handling

---

## Project Structure

```text
hipi_automation_2.0/
├── base/
│   └── base_test.py
├── config/
│   ├── config.py
│   ├── device_config.py
│   └── environments.py
├── core/
│   ├── cloud_driver_factory.py
│   ├── driver_factory.py
│   └── popup_handler.py
├── locators/
│   ├── feed_locators.py
│   └── login_locators.py
├── pages/
│   ├── base_page.py
│   ├── feed_page.py
│   └── login_page.py
├── reports/
│   ├── allure-results/
│   ├── html/
│   └── screenshots/
├── testdata/
│   └── test_data.py
├── tests/
│   ├── test_feed.py
│   └── test_login.py
├── utils/
│   ├── gestures.py
│   ├── logger.py
│   └── screenshot_utils.py
├── .env
├── .gitignore
├── conftest.py
├── pytest.ini
├── RECOMMENDATIONS.md
├── requirements.txt
├── run_tests.sh
└── README.md
```

---

## Core Architecture

### 1. Driver Management

The driver lifecycle is centrally controlled in:

- `conftest.py`
- `core/driver_factory.py`
- `config/device_config.py`
- `config/environments.py`

These files handle:

- Appium server configuration
- Android device selection
- Environment selection (`qa`, `staging`, `production`)
- App package and activity configuration
- Retry logic for session creation
- Shared feed-session reuse and recovery
- App reset and relaunch logic

### 2. Page Object Model

Pages are separated into reusable UI classes:

- `pages/login_page.py` — login flow, home detection, OTP entry, already-logged-in checks
- `pages/feed_page.py` — feed readiness, like/comment/share/save/mute/pause actions
- `pages/base_page.py` — common helper methods such as clicks, waits, retries, system dialog handling, and app recovery

### 3. Test Layout

Test suites are organized in:

- `tests/test_login.py` — authentication, OTP, and session-related tests
- `tests/test_feed.py` — feed and reel actions, social actions, video controls, and navigation flows

### 4. Test Data and Environment Variables

- `testdata/test_data.py` loads credentials from `.env`
- `config/config.py` provides environment-driven Appium settings
- `.env` should contain required credentials like `TEST_PHONE` and `TEST_OTP`

---

## Prerequisites

Before running the suite, make sure the following are installed and configured:

- Python 3.9+
- Appium server
- Android emulator or a physical Android device
- ADB available in PATH
- Valid HiPi app package installed on the target device/emulator
- Internet access for Appium connection to the device

### Install Python dependencies

```bash
pip install -r requirements.txt
```

### Start Appium

```bash
appium --address 127.0.0.1 --port 4723
```

### Create environment file

Create a `.env` file in the project root with the required values:

```env
TEST_PHONE=9876543210
TEST_OTP=5186
```

> The project is designed to fail early with a clear credential error if these values are missing.

---

## Running Tests

### Using the provided shell wrapper

```bash
./run_tests.sh emulator qa smoke
```

Example commands:

```bash
./run_tests.sh emulator qa regression
./run_tests.sh emulator qa login
./run_tests.sh emulator qa feed
./run_tests.sh emulator qa feed_e2e
```

### Direct pytest usage

```bash
pytest tests/ --device emulator --env qa -m smoke
pytest tests/test_login.py --device emulator --env qa
pytest tests/test_feed.py --device emulator --env qa -m feed
```

---

## Pytest Markers

The suite uses these custom markers:

- `smoke` — quick validation set
- `sanity` — alias of smoke, kept for compatibility
- `regression` — full validation set
- `login` — authentication and session coverage
- `feed` — feed and reel interactions
- `feed_e2e` — long-running end-to-end flow
- `requires_logout` — forces app data reset before a test that requires a logged-out state

These markers are configured in `pytest.ini`.

---

## Configuration and Environment Support

The framework supports multiple device and environment configurations through:

- `config/device_config.py`
- `config/environments.py`

Available example devices include:

- `emulator`
- `real_device_1`
- `real_device_2`
- `ios_simulator` (placeholder)
- `ios_real_device` (placeholder)

Available environments include:

- `qa`
- `staging`
- `production`

---

## Reporting

The project generates both HTML and Allure reports.

### Report folders

- `reports/allure-results/`
- `reports/allure-report/`
- `reports/html/report.html`
- `reports/screenshots/`

### Open Allure report locally

```bash
allure serve reports/allure-results
```

---

## Failure Handling and Recovery

The framework contains several reliability improvements:

- automatic Appium driver retries
- Appium UiAutomator2 cleanup before driver creation
- app-data clear for tests marked `requires_logout`
- session reuse for feed tests with liveness checks
- recovery from permission dialogs and app state drift
- full page-source and screenshot capture on failure

This makes the suite more resilient against flaky Android session behavior and transient UI interruptions.

---

## Notes

- The app is treated as a Compose-based Android app and the locators are designed around the current UI structure.
- The suite uses `NO_RESET=true` in the default configuration for speed, but specific tests can explicitly trigger logout resets.
- The project is intended for Android-first mobile validation, with iOS entries present as placeholders rather than fully validated automation paths.

---

## Recommended Workflow

1. Start Appium
2. Start an emulator or connect a real Android device
3. Configure `.env` with valid credentials
4. Run smoke tests first
5. Run feed/login/regression suites as needed
6. Review the generated report in Allure or HTML output

---

## Summary

This repository is a practical, resilient Appium automation framework for testing the HiPi mobile app. It combines good automation practices such as POM, environment-based config, reusable fixtures, retry logic, and rich reporting to support regular functional validation of the Android app.
