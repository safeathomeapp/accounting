/**
 * Babel Configuration for Accountancy Mobile App
 *
 * Babel is the JavaScript compiler that transforms our TypeScript/JSX code
 * into JavaScript that can run on Android and iOS.
 *
 * Key plugins:
 * - @react-native: Handles React Native specific transformations
 * - react-native-reanimated: Enables high-performance animations
 * - expo-router: Enables file-based routing similar to Next.js
 */

module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      // This preset handles all the JSX and TypeScript transformations
      ['babel-preset-expo'],
    ],
    plugins: [
      // Required for React Native Reanimated (smooth animations)
      'react-native-reanimated/plugin',

      // This plugin is last, as required by reanimated
    ],
  };
};
