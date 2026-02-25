#!/usr/bin/env node

/**
 * Mobile Camera Testing Setup Script
 * 
 * This script helps set up mobile device testing by:
 * 1. Detecting local IP address
 * 2. Generating QR codes for easy mobile access
 * 3. Providing testing URLs
 * 4. Checking network connectivity
 */

import { networkInterfaces } from 'os';

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  blue: '\x1b[34m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  red: '\x1b[31m'
};

function getLocalIPAddress() {
  const nets = networkInterfaces();
  const results = [];

  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      // Skip internal (i.e. 127.0.0.1) and non-IPv4 addresses
      const familyV4Value = typeof net.family === 'string' ? 'IPv4' : 4;
      if (net.family === familyV4Value && !net.internal) {
        results.push({
          interface: name,
          address: net.address
        });
      }
    }
  }

  return results;
}

function generateQRCodeURL(url) {
  // Using Google Charts API for QR code generation
  return `https://chart.googleapis.com/chart?cht=qr&chs=300x300&chl=${encodeURIComponent(url)}`;
}

function printBanner() {
  console.log('\n' + colors.bright + colors.cyan + '╔════════════════════════════════════════════════════════════╗');
  console.log('║                                                            ║');
  console.log('║           Mobile Camera Testing Setup                    ║');
  console.log('║                  Hedera Flow MVP                           ║');
  console.log('║                                                            ║');
  console.log('╚════════════════════════════════════════════════════════════╝' + colors.reset);
  console.log();
}

function printInstructions() {
  console.log(colors.bright + '📋 Testing Instructions:' + colors.reset);
  console.log();
  console.log('1. Ensure your mobile device is on the same WiFi network');
  console.log('2. Open the URL below on your mobile device');
  console.log('3. Follow the test cases in docs/MOBILE_CAMERA_TESTING_GUIDE.md');
  console.log('4. Document results using the provided template');
  console.log();
}

function printNetworkInfo() {
  const ips = getLocalIPAddress();
  
  if (ips.length === 0) {
    console.log(colors.red + '❌ No network interfaces found!' + colors.reset);
    console.log('   Make sure you are connected to a network.');
    return;
  }

  console.log(colors.bright + '🌐 Network Information:' + colors.reset);
  console.log();

  ips.forEach((ip, index) => {
    console.log(colors.green + `   Interface ${index + 1}: ${ip.interface}` + colors.reset);
    console.log(`   IP Address: ${colors.bright}${ip.address}${colors.reset}`);
    console.log();
  });
}

function printTestingURLs(port = 5173) {
  const ips = getLocalIPAddress();
  
  if (ips.length === 0) return;

  console.log(colors.bright + '🔗 Testing URLs:' + colors.reset);
  console.log();

  // Localhost (for desktop testing)
  console.log(colors.yellow + '   Desktop (localhost):' + colors.reset);
  console.log(`   ${colors.bright}http://localhost:${port}${colors.reset}`);
  console.log();

  // Network URLs (for mobile testing)
  ips.forEach((ip, index) => {
    const url = `http://${ip.address}:${port}`;
    console.log(colors.yellow + `   Mobile (${ip.interface}):` + colors.reset);
    console.log(`   ${colors.bright}${url}${colors.reset}`);
    console.log();
    
    // QR Code URL
    const qrUrl = generateQRCodeURL(url);
    console.log(colors.cyan + '   📱 QR Code (scan with mobile):' + colors.reset);
    console.log(`   ${qrUrl}`);
    console.log();
  });
}

function printTestCases() {
  console.log(colors.bright + '✅ Quick Test Checklist:' + colors.reset);
  console.log();
  console.log('   [ ] Camera starts on iOS Safari');
  console.log('   [ ] Camera starts on Android Chrome');
  console.log('   [ ] Back camera is used by default');
  console.log('   [ ] Alignment guide is visible');
  console.log('   [ ] Photo capture works');
  console.log('   [ ] File is created with correct name');
  console.log('   [ ] Metadata includes timestamp');
  console.log('   [ ] GPS data captured (if permission granted)');
  console.log('   [ ] Camera stops after capture');
  console.log('   [ ] Cancel button works');
  console.log('   [ ] Close button works');
  console.log('   [ ] Error message shows if permission denied');
  console.log('   [ ] UI is responsive on small screens');
  console.log('   [ ] Touch targets are large enough');
  console.log('   [ ] No crashes or freezes');
  console.log();
}

function printTroubleshooting() {
  console.log(colors.bright + '🔧 Troubleshooting:' + colors.reset);
  console.log();
  console.log('   • If mobile device cannot connect:');
  console.log('     - Check both devices are on same WiFi network');
  console.log('     - Disable firewall temporarily');
  console.log('     - Try different network interface IP');
  console.log();
  console.log('   • If camera permission not requested:');
  console.log('     - Ensure using HTTPS or localhost');
  console.log('     - Clear browser cache and site data');
  console.log('     - Try different browser');
  console.log();
  console.log('   • For HTTPS testing (production-like):');
  console.log('     - Use ngrok: npx ngrok http 5173');
  console.log('     - Use localtunnel: npx localtunnel --port 5173');
  console.log();
}

function printResources() {
  console.log(colors.bright + '📚 Resources:' + colors.reset);
  console.log();
  console.log('   • Testing Guide: docs/MOBILE_CAMERA_TESTING_GUIDE.md');
  console.log('   • Camera Component: src/components/Camera.tsx');
  console.log('   • Integration Tests: src/components/__tests__/Camera.integration.test.tsx');
  console.log();
}

function printFooter() {
  console.log(colors.bright + '═══════════════════════════════════════════════════════════' + colors.reset);
  console.log();
  console.log(colors.green + '✨ Ready to test! Open the URL on your mobile device.' + colors.reset);
  console.log();
  console.log(colors.cyan + '💡 Tip: Use the QR code for quick access on mobile devices.' + colors.reset);
  console.log();
}

// Main execution
function main() {
  const port = process.argv[2] || 5173;

  printBanner();
  printInstructions();
  printNetworkInfo();
  printTestingURLs(port);
  printTestCases();
  printTroubleshooting();
  printResources();
  printFooter();
}

main();
