import React, { useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, StatusBar, Dimensions,
} from 'react-native';
import { useAppStore } from '../store/appStore';
import { toolBridge } from '../bridge/python';

const { width } = Dimensions.get('window');

const CATEGORIES = [
  { id: 'wireless', icon: '📡', label: 'Wireless', color: '#ff6b6b' },
  { id: 'network', icon: '🌐', label: 'Network', color: '#4ecdc4' },
  { id: 'web', icon: '🔍', label: 'Web', color: '#45b7d1' },
  { id: 'password', icon: '🔓', label: 'Password', color: '#f9ca24' },
  { id: 'traffic', icon: '🔗', label: 'Traffic', color: '#6c5ce7' },
  { id: 'device', icon: '📹', label: 'Device', color: '#a29bfe' },
  { id: 'android', icon: '📱', label: 'Android', color: '#00b894' },
  { id: 'osint', icon: '🕵️', label: 'OSINT', color: '#fd79a8' },
  { id: 'forensic', icon: '🔬', label: 'Forensic', color: '#e17055' },
  { id: 'system', icon: '⚙️', label: 'System', color: '#636e72' },
];

export function HomeScreen({ navigation }: any) {
  const { rooted, totalTools, availableTools, loadStatus } = useAppStore();

  useEffect(() => {
    toolBridge.connect();
    loadStatus();
    const interval = setInterval(loadStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0a0a0f" />
      <View style={styles.header}>
        <Text style={styles.title}>CyberLab Pro</Text>
        <Text style={styles.subtitle}>v3.0 · Security Assessment Suite</Text>
        <View style={styles.statusBar}>
          <View style={[styles.statusDot, { backgroundColor: rooted ? '#00ff88' : '#ff6b6b' }]} />
          <Text style={styles.statusText}>{rooted ? 'Rooted' : 'No Root'}</Text>
          <Text style={styles.statusSep}>|</Text>
          <Text style={styles.statusText}>{availableTools}/{totalTools} tools</Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.grid}>
        {CATEGORIES.map((cat) => (
          <TouchableOpacity
            key={cat.id}
            style={[styles.card, { borderColor: cat.color + '40' }]}
            onPress={() => navigation.navigate('Category', { category: cat.id, label: cat.label })}
            activeOpacity={0.7}
          >
            <Text style={styles.cardIcon}>{cat.icon}</Text>
            <Text style={styles.cardLabel}>{cat.label}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0f' },
  header: { paddingTop: 50, paddingHorizontal: 20, paddingBottom: 16, borderBottomWidth: 1, borderBottomColor: '#1a1a2e' },
  title: { fontSize: 28, fontWeight: 'bold', color: '#ffffff' },
  subtitle: { fontSize: 12, color: '#888', marginTop: 2 },
  statusBar: { flexDirection: 'row', alignItems: 'center', marginTop: 8 },
  statusDot: { width: 8, height: 8, borderRadius: 4, marginRight: 6 },
  statusText: { fontSize: 12, color: '#aaa' },
  statusSep: { marginHorizontal: 8, color: '#444' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', padding: 12 },
  card: {
    width: (width - 36) / 2, margin: 6, padding: 20, borderRadius: 16,
    borderWidth: 1, backgroundColor: '#12121a', alignItems: 'center',
  },
  cardIcon: { fontSize: 36, marginBottom: 8 },
  cardLabel: { fontSize: 14, fontWeight: '600', color: '#ddd' },
});
