# BLE Connection Behavior — Test Checklist

Before implementing persistent connection support, we need to understand how the
JuTai device behaves with nRF Connect. Run these tests and note the results.

## Setup

- App: **nRF Connect** (iOS or Android)
- Device: JuTai / Lumineo BLE LED light string
- Connect to the device and navigate to the GATT characteristic:
  `0000fff1-0000-1000-8000-00805f9b34fb`

---

## Test 1 — Does brightness command alone turn on the device?

**Goal:** Find out if we can replace two commands (ON + brightness) with just one.

1. Make sure the light is **OFF**
2. Send brightness command **without** sending ON first:
   - 50% brightness: `574C5402093200`
3. **Observe:** Does the light turn on?

| Result | Note |
|--------|------|
| ☐ Yes, light turns on at 50% | Can skip separate ON command |
| ☐ No, light stays off | ON command is required before brightness |

---

## Test 2 — Does the device accept multiple commands without reconnecting?

**Goal:** Confirm the device supports persistent connections.

1. Connect with nRF Connect (stay connected)
2. Send ON command: `574C54021101`
3. **Without disconnecting**, send brightness 25%: `574C5402091900`
4. **Without disconnecting**, send brightness 75%: `574C5402094B00`
5. **Without disconnecting**, send OFF: `574C54021102`

| Result | Note |
|--------|------|
| ☐ All commands worked | Device supports persistent connection |
| ☐ Failed after first command | Device drops connection after write |
| ☐ Failed after N seconds | Device has idle timeout (~__ seconds) |

---

## Test 3 — How long does the device stay connected when idle?

**Goal:** Determine idle timeout to set our disconnect timer correctly.

1. Connect with nRF Connect
2. Send ON command: `574C54021101`
3. Do nothing — watch when nRF Connect shows disconnected
4. Note the time until disconnect

| Result |
|--------|
| ☐ Never disconnects (stays connected indefinitely) |
| ☐ Disconnects after ~__ seconds / minutes |
| ☐ Only disconnects when phone screen locks |

---

## Test 4 — Can we reconnect and send a command immediately after idle disconnect?

**Goal:** Validate our reconnect strategy.

1. Let the device disconnect from Test 3
2. Immediately reconnect and send ON: `574C54021101`
3. **Observe:** Does it respond without issues?

| Result |
|--------|
| ☐ Yes, reconnects and responds fine |
| ☐ Needs a short delay before first command after reconnect |
| ☐ Requires power cycle to accept connection again |

---

## Results Summary

Fill in after testing and add as a comment to PR #4.
