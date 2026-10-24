import React, { useState } from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import * as Clipboard from 'expo-clipboard';
import { Copy, Check } from 'lucide-react-native';
import { truncateAddress } from '../../utils/format';
import { Colors } from '../../constants/colors';

interface AddressDisplayProps {
  address: string;
}

export const AddressDisplay: React.FC<AddressDisplayProps> = ({ address }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await Clipboard.setStringAsync(address);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <TouchableOpacity
      activeOpacity={0.7}
      onPress={handleCopy}
      style={styles.container}
    >
      <Text style={styles.addressText}>{truncateAddress(address)}</Text>
      {copied ? (
        <Check size={14} color={Colors.light.primary} />
      ) : (
        <Copy size={14} color={Colors.light.secondaryText} />
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.light.paper,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.light.hairline,
  },
  addressText: {
    fontFamily: 'monospace',
    fontSize: 13,
    color: Colors.light.ink,
    marginRight: 6,
  },
});
