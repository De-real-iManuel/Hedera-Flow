# Hedera DNS Resolution Fix

## Issue
Java's DNS resolver in the Hedera SDK fails to resolve `testnet.mirrornode.hedera.com` on Windows, causing warnings:
```
java.net.UnknownHostException: testnet.mirrornode.hedera.com
```

## Root Cause
- Java's built-in DNS resolver has issues with certain Windows network configurations
- The hostname resolves fine in PowerShell/Windows but fails in JVM
- This is a known Java networking issue on Windows

## Solutions

### Solution 1: Add to Windows Hosts File (Recommended)

1. Open Notepad as Administrator
2. Open file: `C:\Windows\System32\drivers\etc\hosts`
3. Add this line at the end:
   ```
   35.186.230.203 testnet.mirrornode.hedera.com
   ```
4. Save and restart your backend server

### Solution 2: Use IPv4 Preference (Alternative)

Add this to your Python startup (before importing Hedera):
```python
import os
os.environ['JAVA_TOOL_OPTIONS'] = '-Djava.net.preferIPv4Stack=true'
```

### Solution 3: Disable IPv6 (System-wide)

1. Open PowerShell as Administrator
2. Run:
   ```powershell
   Disable-NetAdapterBinding -Name "*" -ComponentID ms_tcpip6
   ```
3. Restart your computer

## Current Status

The warnings don't prevent the application from working, but they:
- Clutter the logs
- May cause delays in Hedera operations
- Could lead to timeouts in some cases

## Verification

After applying a fix, you should see:
```
✅ Hedera client initialized with operator: 0.0.7942971
```

Without the DNS warnings.

## Impact on Application

- The 404 errors for `/verify/scan` have been fixed (endpoint added)
- The DNS warnings are non-critical but should be resolved for production
- All other functionality works correctly
