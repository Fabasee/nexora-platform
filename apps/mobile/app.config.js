const fs = require("node:fs");
const path = require("node:path");

module.exports = ({ config }) => {
  const androidServicesPath = path.join(__dirname, "google-services.json");
  const iosServicesPath = path.join(__dirname, "GoogleService-Info.plist");

  const expo = {
    ...config,
    android: {
      ...config.android,
      package: config.android?.package ?? "com.nexora.platform.mobile",
    },
    ios: {
      ...config.ios,
      bundleIdentifier: config.ios?.bundleIdentifier ?? "com.nexora.platform.mobile",
    },
    plugins: [
      ...(config.plugins ?? []),
      "expo-dev-client",
      "@react-native-firebase/app",
      "@react-native-firebase/auth",
      [
        "expo-build-properties",
        {
          ios: {
            useFrameworks: "dynamic",
          },
        },
      ],
    ],
  };

  if (fs.existsSync(androidServicesPath)) {
    expo.android.googleServicesFile = "./google-services.json";
  } else {
    delete expo.android.googleServicesFile;
  }

  if (fs.existsSync(iosServicesPath)) {
    expo.ios.googleServicesFile = "./GoogleService-Info.plist";
  } else {
    delete expo.ios.googleServicesFile;
  }

  return expo;
};
