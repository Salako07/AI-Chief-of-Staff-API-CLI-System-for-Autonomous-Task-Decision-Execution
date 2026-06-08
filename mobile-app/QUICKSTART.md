# Quick Start Guide - AI Chief of Staff Mobile App

## Prerequisites

- Node.js 18+ installed
- React Native development environment set up:
  - **iOS:** Xcode 14+ (Mac only)
  - **Android:** Android Studio with SDK
- Backend API running on `http://localhost:8000`

## Step 1: Install Dependencies

```bash
cd mobile-app
npm install
```

## Step 2: iOS Setup (Mac only)

```bash
cd ios
pod install
cd ..
```

## Step 3: Configure API URL

**IMPORTANT:** If testing on a real device (not simulator/emulator), update the API URL.

Edit `src/api/client.ts`:

```typescript
const API_BASE_URL = __DEV__
  ? 'http://YOUR_COMPUTER_IP:8000'  // Replace with your IP
  : 'https://api.yourcompany.com';
```

### Find Your Computer's IP Address:

**Windows:**
```bash
ipconfig
```
Look for "IPv4 Address" under your active network adapter (e.g., `192.168.1.100`)

**Mac/Linux:**
```bash
ifconfig
# or
ip addr
```
Look for `inet` address (e.g., `192.168.1.100`)

**Example:**
```typescript
const API_BASE_URL = 'http://192.168.1.100:8000'
```

## Step 4: Start Backend

Make sure your backend is running:

```bash
# In the project root directory
docker-compose up
```

Verify backend is accessible:
- Open browser: `http://localhost:8000/docs`
- Should see FastAPI Swagger docs

## Step 5: Run Mobile App

### iOS (Simulator):

```bash
npm run ios
```

Or select device in Xcode and click Run.

### Android (Emulator):

```bash
npm run android
```

Or open Android Studio, select device, and click Run.

### Real Devices:

1. **Update API URL** with your computer's IP (see Step 3)
2. **Connect device via USB**
3. **Enable Developer Mode:**
   - iOS: Settings → General → VPN & Device Management
   - Android: Settings → About Phone → Tap "Build Number" 7 times
4. **Trust computer on device**
5. **Run app:**
   ```bash
   npm run ios    # iOS
   npm run android # Android
   ```

## Testing the App

### 1. Test Video Upload

1. Navigate to **Record** tab
2. Tap **Upload File** button
3. Select a video/audio file
4. Watch upload progress
5. Wait for transcription to complete
6. View results (tasks, decisions, risks)

### 2. Test Text Processing

1. Navigate to **Process** tab (Text icon)
2. Enter or paste meeting notes
3. Tap **Process Text**
4. View extracted tasks, decisions, and risks

### 3. View Dashboard

1. Navigate to **Dashboard** tab
2. See stats: total tasks, decisions, risks
3. Browse recent tasks
4. Tap task cards to view details

## Troubleshooting

### "Network Request Failed"

**Problem:** App can't reach backend API

**Solutions:**
1. Verify backend is running: `docker-compose ps`
2. Check API URL in `src/api/client.ts`
3. For real devices: Use computer's IP, not localhost
4. Ensure device and computer on same Wi-Fi network
5. Check firewall settings (allow port 8000)

### Metro Bundler Issues

```bash
npm start -- --reset-cache
```

### iOS Build Fails

```bash
cd ios
rm -rf Pods Podfile.lock
pod install
cd ..
```

### Android Build Fails

```bash
cd android
./gradlew clean
cd ..
npm run android
```

### "Module not found" Errors

```bash
rm -rf node_modules
npm install
```

## Current Features

✅ **Working:**
- Video/audio upload with progress tracking
- Transcription status polling
- Text processing
- Dashboard with stats
- Results viewing (tasks, decisions, risks)
- Navigation between screens

⚠️ **Not Implemented Yet:**
- Authentication (bypassed for now)
- Camera recording (placeholder only)
- Video playback
- Task editing/assignment
- Push notifications

## API Endpoints Used

The app connects to these backend endpoints:

### Media:
- `POST /api/v1/media/upload` - Upload video/audio
- `POST /api/v1/media/transcribe/{media_id}` - Start transcription
- `GET /api/v1/media/status/{job_id}` - Check status
- `GET /api/v1/media/result/{job_id}` - Get results

### Text Processing:
- `POST /api/v1/process` - Process text input

### Health:
- `GET /api/v1/media/health` - Backend health check

## Project Structure

```
mobile-app/
├── src/
│   ├── api/           # API client and services
│   ├── components/    # Reusable UI components
│   ├── navigation/    # React Navigation setup
│   ├── screens/       # App screens
│   ├── stores/        # Zustand state management
│   └── types/         # TypeScript types
├── App.tsx            # Entry point
└── package.json       # Dependencies
```

## Next Steps

1. **Test video upload** - Verify full upload → transcription → results flow
2. **Test text processing** - Confirm AI extraction works
3. **Implement camera recording** - Add react-native-vision-camera
4. **Add authentication** - When backend auth endpoints are ready
5. **Polish UI** - Enhance animations and interactions

## Need Help?

- Check backend logs: `docker-compose logs -f`
- Check mobile app logs: Look at Metro bundler terminal
- iOS logs: Xcode → Window → Devices and Simulators
- Android logs: `adb logcat`

## Development Tips

- **Hot Reload:** Shake device or press Cmd+D (iOS) / Cmd+M (Android)
- **React DevTools:** Install React Native Debugger
- **Network Debugging:** Use Flipper or Charles Proxy
- **State Inspection:** Use Flipper or Redux DevTools (for Zustand)

Happy coding! 🚀
