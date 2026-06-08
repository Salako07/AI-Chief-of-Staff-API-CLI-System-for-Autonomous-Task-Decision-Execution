# AI Chief of Staff - Mobile App

React Native mobile application for the AI Chief of Staff system. Transform meetings into actionable tasks with AI-powered extraction from video, audio, and text.

## 🚀 Quick Start

**New to the app?** Start with [QUICKSTART.md](./QUICKSTART.md) for a step-by-step guide!

## ⚠️ Current Status

**Authentication Disabled:** The app currently bypasses authentication and goes directly to the main interface. This allows you to test core features (video upload, transcription, text processing) without implementing backend auth endpoints first.

## Features

- **Video/Audio Recording & Upload**: Capture meetings directly or upload existing files
- **AI-Powered Extraction**: Automatically extract tasks, decisions, and risks
- **Real-time Processing**: Track upload and transcription progress in real-time
- **Text Processing**: Process meeting notes and transcripts via text input
- **Dashboard**: View stats, tasks, decisions, and risks at a glance
- **Cross-Platform**: Works on both iOS and Android

## Tech Stack

- **React Native 0.73** - Cross-platform mobile framework
- **TypeScript** - Type-safe development
- **React Navigation** - Navigation library
- **Zustand** - State management
- **Axios** - HTTP client
- **React Native Vector Icons** - Icon library
- **React Native Vision Camera** - Camera integration (planned)

## Project Structure

```
mobile-app/
├── src/
│   ├── api/                    # API client and services
│   │   ├── client.ts          # Base API client with auth
│   │   ├── auth.ts            # Authentication endpoints
│   │   ├── media.ts           # Video/audio upload and transcription
│   │   ├── text.ts            # Text processing
│   │   └── index.ts           # API exports
│   ├── components/            # Reusable UI components
│   │   ├── TaskCard.tsx
│   │   ├── DecisionCard.tsx
│   │   ├── RiskCard.tsx
│   │   ├── VideoCard.tsx
│   │   ├── ProgressBar.tsx
│   │   ├── EmptyState.tsx
│   │   └── index.ts
│   ├── navigation/            # Navigation setup
│   │   ├── types.ts           # Navigation type definitions
│   │   ├── AppNavigator.tsx   # Root navigator
│   │   ├── AuthNavigator.tsx  # Auth flow
│   │   ├── MainNavigator.tsx  # Main tab navigator
│   │   ├── DashboardNavigator.tsx
│   │   ├── RecordNavigator.tsx
│   │   └── ProcessNavigator.tsx
│   ├── screens/               # App screens
│   │   ├── auth/              # Authentication screens
│   │   │   ├── WelcomeScreen.tsx
│   │   │   ├── LoginScreen.tsx
│   │   │   └── SignupScreen.tsx
│   │   ├── dashboard/         # Dashboard screens
│   │   │   ├── DashboardHomeScreen.tsx
│   │   │   ├── VideoDetailsScreen.tsx
│   │   │   ├── TranscriptionResultScreen.tsx
│   │   │   └── TaskDetailsScreen.tsx
│   │   ├── record/            # Video recording screens
│   │   │   ├── RecordVideoScreen.tsx
│   │   │   ├── UploadProgressScreen.tsx
│   │   │   └── ProcessingStatusScreen.tsx
│   │   ├── process/           # Text processing screens
│   │   │   ├── TextInputScreen.tsx
│   │   │   └── ProcessingResultScreen.tsx
│   │   └── main/              # Main screens
│   │       └── ProfileScreen.tsx
│   ├── stores/                # Zustand state management
│   │   ├── authStore.ts       # Authentication state
│   │   ├── uploadStore.ts     # Upload management
│   │   └── resultsStore.ts    # Results and videos
│   └── types/                 # TypeScript types
│       └── api.ts             # API response types
├── App.tsx                    # App entry point
├── package.json
├── tsconfig.json
├── babel.config.js
└── metro.config.js
```

## Installation

### Prerequisites

- Node.js 18+ and npm/yarn
- React Native CLI
- Xcode (for iOS development)
- Android Studio (for Android development)

### Setup

1. **Install dependencies:**
   ```bash
   cd mobile-app
   npm install
   ```

2. **iOS Setup:**
   ```bash
   cd ios
   pod install
   cd ..
   ```

3. **Configure API URL:**

   Update the API base URL in `src/api/client.ts`:
   ```typescript
   const API_BASE_URL = __DEV__
     ? 'http://YOUR_COMPUTER_IP:8000'  // Replace with your IP for real devices
     : 'https://api.yourcompany.com';  // Production URL
   ```

4. **Run the app:**

   **iOS:**
   ```bash
   npm run ios
   ```

   **Android:**
   ```bash
   npm run android
   ```

## Configuration

### Environment Variables

The app uses the following configuration in `src/api/client.ts`:

- `API_BASE_URL` - Backend API base URL
- `TOKEN_KEY` - AsyncStorage key for access token
- `REFRESH_TOKEN_KEY` - AsyncStorage key for refresh token

### Camera Permissions

For video recording, you'll need to add camera permissions:

**iOS (Info.plist):**
```xml
<key>NSCameraUsageDescription</key>
<string>We need camera access to record meeting videos</string>
<key>NSMicrophoneUsageDescription</key>
<string>We need microphone access to record meeting audio</string>
```

**Android (AndroidManifest.xml):**
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
```

## State Management

The app uses Zustand for state management with three main stores:

### Auth Store (`authStore.ts`)
- User authentication state
- Login/signup/logout actions
- Token management

### Upload Store (`uploadStore.ts`)
- Active uploads tracking
- Upload progress monitoring
- Transcription status polling

### Results Store (`resultsStore.ts`)
- Transcription results
- Video metadata
- Tasks, decisions, and risks aggregation

## API Integration

All API calls go through the centralized client in `src/api/client.ts`:

### Features:
- **Automatic token refresh** - Refreshes expired access tokens
- **Request/response interceptors** - Auto-adds auth headers
- **Error handling** - Consistent error formatting
- **File uploads** - Progress tracking for video uploads
- **TypeScript types** - Fully typed API responses

### API Services:

**Auth (`auth.ts`):**
- `login(credentials)` - User login
- `signup(data)` - User registration
- `logout()` - User logout
- `getCurrentUser()` - Fetch current user profile

**Media (`media.ts`):**
- `uploadMedia(file, onProgress)` - Upload video/audio with progress
- `startTranscription(mediaId)` - Start AI transcription job
- `getTranscriptionStatus(jobId)` - Check transcription status
- `getTranscriptionResult(jobId)` - Get final results
- `pollTranscriptionStatus(jobId, onProgress)` - Auto-poll until complete
- `getVideoMetadata(mediaId)` - Get video details
- `getVideoUrl(mediaId)` - Get presigned playback URL
- `deleteVideo(mediaId)` - Delete video

**Text (`text.ts`):**
- `processText(text)` - Process text input
- `processFile(file, onProgress)` - Process text file upload

## Navigation Flow

```
AppNavigator (Root)
├── Auth Stack (Not Authenticated)
│   ├── Welcome
│   ├── Login
│   └── Signup
└── Main Tabs (Authenticated)
    ├── Dashboard Stack
    │   ├── Dashboard Home
    │   ├── Video Details
    │   ├── Transcription Result
    │   └── Task Details
    ├── Record Stack
    │   ├── Record Video
    │   ├── Upload Progress
    │   └── Processing Status
    ├── Process Stack
    │   ├── Text Input
    │   └── Processing Result
    └── Profile (Single Screen)
```

## Development Workflow

### Running on Real Devices

For iOS:
1. Connect iPhone via USB
2. Select device in Xcode
3. Run `npm run ios`

For Android:
1. Enable USB debugging on Android device
2. Connect via USB
3. Run `adb devices` to verify connection
4. Run `npm run android`

**Important:** Update the API URL to your computer's local IP address (not localhost) when testing on real devices.

### Debugging

- **React Native Debugger** - Recommended for debugging
- **Flipper** - Built-in debugging tool
- **Chrome DevTools** - For JavaScript debugging

Enable debug menu:
- iOS: Cmd + D
- Android: Cmd + M (Mac) or Ctrl + M (Windows/Linux)

## Backend Requirements

The mobile app requires the following backend endpoints to be implemented:

### Authentication Endpoints (TO BE ADDED)
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update user profile

### Existing Media Endpoints (WORKING)
- `POST /api/v1/media/upload` - Upload video/audio
- `POST /api/v1/media/transcribe/{media_id}` - Start transcription
- `GET /api/v1/media/status/{job_id}` - Get transcription status
- `GET /api/v1/media/result/{job_id}` - Get transcription result
- `GET /api/v1/media/video/{media_id}/metadata` - Get video metadata
- `GET /api/v1/media/video/{media_id}/url` - Get presigned URL
- `DELETE /api/v1/media/video/{media_id}` - Delete video

### Text Processing Endpoint (EXISTING)
- `POST /api/v1/process` - Process text input

## UI Design

The app follows a dark theme design system:

### Colors
- **Background:** #000000 (Black)
- **Cards:** #1F2937 (Dark Gray)
- **Borders:** #374151 (Gray)
- **Primary:** #3B82F6 (Blue)
- **Success:** #10B981 (Green)
- **Warning:** #F59E0B (Orange)
- **Error:** #EF4444 (Red)
- **Text Primary:** #FFFFFF (White)
- **Text Secondary:** #9CA3AF (Light Gray)

### Typography
- **Title:** 32px, Bold
- **Heading:** 20-24px, Semibold
- **Body:** 14-16px, Regular
- **Caption:** 12px, Regular

## Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run linter
npm run lint

# Run type checker
npm run type-check
```

## Building for Production

### iOS

1. Open Xcode project
2. Select "Generic iOS Device"
3. Product → Archive
4. Follow App Store submission process

### Android

```bash
cd android
./gradlew assembleRelease
```

APK will be in `android/app/build/outputs/apk/release/`

## Troubleshooting

### Common Issues

**Metro bundler issues:**
```bash
npm start -- --reset-cache
```

**iOS build fails:**
```bash
cd ios
pod deintegrate
pod install
```

**Android build fails:**
```bash
cd android
./gradlew clean
cd ..
npm run android
```

**Network errors on real device:**
- Ensure device and computer are on same Wi-Fi network
- Update API_BASE_URL to use computer's local IP (not localhost)
- Check firewall settings

## Next Steps

### Planned Features
1. **Camera Integration** - Implement video recording with react-native-vision-camera
2. **Push Notifications** - Firebase Cloud Messaging for job completion alerts
3. **Offline Support** - Cache results for offline viewing
4. **Video Playback** - In-app video player for recorded meetings
5. **Task Management** - Edit, assign, and complete tasks within app
6. **Search & Filters** - Search tasks, decisions, and risks
7. **Dark/Light Theme Toggle** - User preference for theme
8. **Multi-language Support** - Internationalization

### Backend Requirements
- Implement authentication endpoints (login, signup, refresh token)
- Add user profile endpoints
- Consider adding pagination for dashboard data
- Add endpoints for task management (update status, assign owner)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Your License Here]

## Support

For issues and questions:
- Open an issue on GitHub
- Contact: support@yourcompany.com
