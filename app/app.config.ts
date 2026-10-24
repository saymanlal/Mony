import { ExpoConfig, ConfigContext } from 'expo/config';

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: 'Mony',
  slug: 'mony',
  version: '1.0.0',
  orientation: 'portrait',
  icon: './assets/icon.png',
  userInterfaceStyle: 'automatic',
  splash: {
    image: './assets/splash.png',
    resizeMode: 'contain',
    backgroundColor: '#F5F2EB',
  },
  updates: {
    fallbackToCacheTimeout: 0,
  },
  assetBundlePatterns: ['**/*'],
  ios: {
    supportsTablet: false,
    bundleIdentifier: 'com.mony.app',
    infoPlist: {
      NSCameraUsageDescription:
        'Mony uses your camera to scan rupee notes for verification.',
      NSFaceIDUsageDescription:
        'Mony uses Face ID to protect your wallet.',
    },
  },
  android: {
    adaptiveIcon: {
      foregroundImage: './assets/adaptive-icon.png',
      backgroundColor: '#F5F2EB',
    },
    package: 'com.mony.app',
    permissions: [
      'CAMERA',
      'USE_BIOMETRIC',
      'USE_FINGERPRINT',
      'VIBRATE',
    ],
  },
  web: {
    favicon: './assets/favicon.png',
  },
  plugins: [
    'expo-router',
    'expo-secure-store',
    'expo-font',
    [
      'expo-local-authentication',
      {
        faceIDPermission: 'Mony uses Face ID to protect your wallet.',
      },
    ],
    [
      'expo-camera',
      {
        cameraPermission: 'Mony uses your camera to scan rupee notes for verification.',
      },
    ],
    [
      'expo-notifications',
      {
        icon: './assets/notification-icon.png',
        color: '#0E4D3C',
      },
    ],
  ],
  experiments: {
    typedRoutes: true,
  },
  extra: {
    eas: {
      projectId: 'mony-app',
    },
  },
});
