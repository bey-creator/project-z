import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, StatusBar,
} from 'react-native';
import { useAppStore } from '../store/appStore';
import { toolBridge } from '../bridge/python';

interface ToolInfo {
  name: string;
  desc: string;
  icon: string;
  available: boolean;
  execution: 'native' | 'python';
}

const TOOLS_BY_CATEGORY: Record<string, ToolInfo[]> = {
  wireless: [
    { name: 'aircrack-ng', desc: 'WiFi security testing suite', icon: '📡', available: false, execution: 'native' },
    { name: 'reaver', desc: 'WPS security testing', icon: '🔑', available: false, execution: 'native' },
    { name: 'pixiewps', desc: 'WPS offline testing', icon: '🔓', available: false, execution: 'native' },
    { name: 'wifite', desc: 'Automated wireless auditor', icon: '📶', available: false, execution: 'python' },
    { name: 'airgeddon', desc: 'Wireless assessment framework', icon: '📻', available: false, execution: 'python' },
  ],
  network: [
    { name: 'nmap', desc: 'Network discovery & scanning', icon: '🌐', available: false, execution: 'native' },
    { name: 'masscan', desc: 'High-speed scanning', icon: '⚡', available: false, execution: 'native' },
    { name: 'tcpdump', desc: 'Packet capture', icon: '📦', available: false, execution: 'native' },
    { name: 'netdiscover', desc: 'Device discovery', icon: '🔍', available: false, execution: 'native' },
    { name: 'responder', desc: 'LLMNR/NBT-NS poisoner', icon: '🎯', available: false, execution: 'native' },
    { name: 'impacket', desc: 'Protocol toolkit', icon: '🧰', available: false, execution: 'python' },
  ],
  web: [
    { name: 'sqlmap', desc: 'SQL injection testing', icon: '💉', available: false, execution: 'python' },
    { name: 'nikto', desc: 'Web server scanner', icon: '🔎', available: false, execution: 'python' },
    { name: 'gobuster', desc: 'Directory brute force', icon: '📂', available: false, execution: 'native' },
    { name: 'ffuf', desc: 'Web fuzzer', icon: '🔫', available: false, execution: 'native' },
    { name: 'wfuzz', desc: 'Web app fuzzer', icon: '🎯', available: false, execution: 'python' },
  ],
  password: [
    { name: 'john', desc: 'Password cracker', icon: '🔓', available: false, execution: 'native' },
    { name: 'hashcat', desc: 'Hash analysis', icon: '🔑', available: false, execution: 'native' },
    { name: 'hydra', desc: 'Online brute force', icon: '💥', available: false, execution: 'native' },
    { name: 'crunch', desc: 'Wordlist generator', icon: '📝', available: false, execution: 'native' },
    { name: 'hash-identifier', desc: 'Hash type detection', icon: '🏷️', available: false, execution: 'python' },
    { name: 'cewl', desc: 'Custom wordlist', icon: '📋', available: false, execution: 'python' },
  ],
  traffic: [
    { name: 'arpspoof', desc: 'ARP spoofing', icon: '🔗', available: false, execution: 'native' },
    { name: 'mitmproxy', desc: 'HTTP/HTTPS intercept', icon: '🕸️', available: false, execution: 'native' },
  ],
  device: [
    { name: 'routersploit', desc: 'Router scanner', icon: '📡', available: false, execution: 'python' },
    { name: 'cameradar', desc: 'Camera assessment', icon: '📹', available: false, execution: 'native' },
    { name: 'searchsploit', desc: 'Vulnerability database', icon: '🗄️', available: false, execution: 'native' },
  ],
  android: [
    { name: 'scrcpy', desc: 'Screen mirroring', icon: '📱', available: false, execution: 'native' },
    { name: 'apktool', desc: 'APK analysis', icon: '📦', available: false, execution: 'native' },
    { name: 'jadx', desc: 'Code decompiler', icon: '☕', available: false, execution: 'native' },
    { name: 'frida', desc: 'Dynamic instrumentation', icon: '🔬', available: false, execution: 'native' },
  ],
  osint: [
    { name: 'maigret', desc: 'Username investigation', icon: '🕵️', available: false, execution: 'python' },
    { name: 'holehe', desc: 'Email verification', icon: '📧', available: false, execution: 'python' },
    { name: 'phoneinfoga', desc: 'Phone analysis', icon: '📞', available: false, execution: 'python' },
    { name: 'photon', desc: 'Website crawler', icon: '🌍', available: false, execution: 'python' },
    { name: 'instaloader', desc: 'Instagram data', icon: '📸', available: false, execution: 'python' },
    { name: 'snscrape', desc: 'Social media scraper', icon: '🐦', available: false, execution: 'python' },
    { name: 'h8mail', desc: 'Breach verification', icon: '🔐', available: false, execution: 'python' },
    { name: 'osintgram', desc: 'Instagram investigation', icon: '📷', available: false, execution: 'python' },
    { name: 'exiftool', desc: 'Metadata extraction', icon: '🏷️', available: false, execution: 'native' },
  ],
  forensic: [
    { name: 'binwalk', desc: 'Firmware analysis', icon: '🔧', available: false, execution: 'python' },
    { name: 'foremost', desc: 'Data recovery', icon: '💾', available: false, execution: 'native' },
    { name: 'volatility', desc: 'Memory analysis', icon: '🧠', available: false, execution: 'python' },
    { name: 'steghide', desc: 'Steganography detect', icon: '🖼️', available: false, execution: 'native' },
  ],
  system: [
    { name: 'lynis', desc: 'Security auditing', icon: '🛡️', available: false, execution: 'native' },
    { name: 'rkhunter', desc: 'Rootkit detection', icon: '🔍', available: false, execution: 'native' },
  ],
};

export function CategoryScreen({ route, navigation }: any) {
  const { category, label } = route.params;
  const { availableTools } = useAppStore();
  const [tools, setTools] = useState<ToolInfo[]>(TOOLS_BY_CATEGORY[category] || []);

  useEffect(() => {
    // Check which tools are actually available
    const checkAvailability = async () => {
      const updated = await Promise.all(
        tools.map(async (tool) => {
          // Would check via bridge if binary/source exists
          return { ...tool, available: true }; // Placeholder
        })
      );
      setTools(updated);
    };
    checkAvailability();
  }, [category]);

  const availableCount = tools.filter((t) => t.available).length;

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0a0a0f" />
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{label}</Text>
        <View style={styles.subHeader}>
          <Text style={styles.subtitle}>{availableCount}/{tools.length} tools available</Text>
          <View style={styles.countBadge}>
            <Text style={styles.countText}>{availableCount}</Text>
          </View>
        </View>
      </View>
      <ScrollView contentContainerStyle={styles.list}>
        {tools.map((tool) => (
          <TouchableOpacity
            key={tool.name}
            style={[styles.toolCard, !tool.available && styles.toolDisabled]}
            onPress={() => {
              if (tool.available) {
                navigation.navigate('Tool', { tool: tool.name, category, execution: tool.execution });
              }
            }}
            disabled={!tool.available}
            activeOpacity={0.7}
          >
            <Text style={styles.toolIcon}>{tool.icon}</Text>
            <View style={styles.toolInfo}>
              <Text style={styles.toolName}>{tool.name}</Text>
              <Text style={styles.toolDesc}>{tool.desc}</Text>
            </View>
            <View style={styles.toolMeta}>
              <View style={[styles.execBadge, tool.execution === 'python' ? styles.execPython : styles.execNative]}>
                <Text style={styles.execText}>{tool.execution === 'python' ? 'PY' : 'BIN'}</Text>
              </View>
              {!tool.available && (
                <Text style={styles.unavailableText}>N/A</Text>
              )}
              {tool.available && <Text style={styles.arrow}>→</Text>}
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0f' },
  header: { paddingTop: 50, paddingHorizontal: 20, paddingBottom: 16, borderBottomWidth: 1, borderBottomColor: '#1a1a2e' },
  backBtn: { marginBottom: 6 },
  backText: { color: '#4ecdc4', fontSize: 14 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff' },
  subHeader: { flexDirection: 'row', alignItems: 'center', marginTop: 4 },
  subtitle: { fontSize: 12, color: '#888' },
  countBadge: { marginLeft: 8, backgroundColor: '#4ecdc4', borderRadius: 10, paddingHorizontal: 8, paddingVertical: 2 },
  countText: { fontSize: 10, color: '#fff', fontWeight: '700' },
  list: { padding: 12 },
  toolCard: {
    flexDirection: 'row', alignItems: 'center', padding: 16, marginBottom: 8,
    backgroundColor: '#12121a', borderRadius: 12, borderWidth: 1, borderColor: '#1a1a2e',
  },
  toolDisabled: { opacity: 0.4, borderColor: '#2a2a3e' },
  toolIcon: { fontSize: 28, marginRight: 14 },
  toolInfo: { flex: 1 },
  toolName: { fontSize: 16, fontWeight: '600', color: '#fff' },
  toolDesc: { fontSize: 12, color: '#888', marginTop: 2 },
  toolMeta: { alignItems: 'flex-end' },
  execBadge: { paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, marginBottom: 4 },
  execPython: { backgroundColor: '#6c5ce7' },
  execNative: { backgroundColor: '#00b894' },
  execText: { fontSize: 9, color: '#fff', fontWeight: '700' },
  unavailableText: { fontSize: 10, color: '#ff6b6b', fontWeight: '600' },
  arrow: { fontSize: 18, color: '#4ecdc4' },
});
