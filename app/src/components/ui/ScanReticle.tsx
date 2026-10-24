import React, { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
} from 'react-native-reanimated';
import { Colors } from '../../constants/colors';

interface ScanReticleProps {
  detected: boolean;
}

export const ScanReticle: React.FC<ScanReticleProps> = ({ detected }) => {
  const bracketOffset = useSharedValue(0);

  useEffect(() => {
    bracketOffset.value = withSpring(detected ? -12 : 0, {
      damping: 15,
      stiffness: 120,
    });
  }, [detected]);

  const cornerTL = useAnimatedStyle(() => ({
    transform: [{ translateX: -bracketOffset.value }, { translateY: -bracketOffset.value }],
  }));

  const cornerTR = useAnimatedStyle(() => ({
    transform: [{ translateX: bracketOffset.value }, { translateY: -bracketOffset.value }],
  }));

  const cornerBL = useAnimatedStyle(() => ({
    transform: [{ translateX: -bracketOffset.value }, { translateY: bracketOffset.value }],
  }));

  const cornerBR = useAnimatedStyle(() => ({
    transform: [{ translateX: bracketOffset.value }, { translateY: bracketOffset.value }],
  }));

  const borderColor = detected ? Colors.light.primary : '#FFFFFF';

  return (
    <View style={styles.container} pointerEvents="none">
      {/* Top Left */}
      <Animated.View
        style={[
          styles.corner,
          styles.topLeft,
          { borderColor },
          cornerTL,
        ]}
      />
      {/* Top Right */}
      <Animated.View
        style={[
          styles.corner,
          styles.topRight,
          { borderColor },
          cornerTR,
        ]}
      />
      {/* Bottom Left */}
      <Animated.View
        style={[
          styles.corner,
          styles.bottomLeft,
          { borderColor },
          cornerBL,
        ]}
      />
      {/* Bottom Right */}
      <Animated.View
        style={[
          styles.corner,
          styles.bottomRight,
          { borderColor },
          cornerBR,
        ]}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: 300,
    height: 160,
    position: 'relative',
    alignSelf: 'center',
    marginVertical: 'auto',
  },
  corner: {
    position: 'absolute',
    width: 32,
    height: 32,
    borderWidth: 3,
  },
  topLeft: {
    top: 0,
    left: 0,
    borderRightWidth: 0,
    borderBottomWidth: 0,
    borderTopLeftRadius: 8,
  },
  topRight: {
    top: 0,
    right: 0,
    borderLeftWidth: 0,
    borderBottomWidth: 0,
    borderTopRightRadius: 8,
  },
  bottomLeft: {
    bottom: 0,
    left: 0,
    borderRightWidth: 0,
    borderTopWidth: 0,
    borderBottomLeftRadius: 8,
  },
  bottomRight: {
    bottom: 0,
    right: 0,
    borderLeftWidth: 0,
    borderTopWidth: 0,
    borderBottomRightRadius: 8,
  },
});
