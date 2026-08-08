import React, { useRef, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';

interface TerminalProps {
  output: string[];
}

export function Terminal({ output }: TerminalProps) {
  const scrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    scrollRef.current?.scrollToEnd({ animated: true });
  }, [output]);

  const colorize = (line: string): string => {
    if (line.includes('[✓]') || line.includes('success')) return '#00ff88';
    if (line.includes('[!]') || line.includes('Error') || line.includes('error')) return '#ff6b6b';
    if (line.includes('[*]')) return '#4ecdc4';
    if (line.includes('[+]')) return '#f9ca24';
    return '#ccc';
  };

  return (
    <View style={styles.container}>
      <View style={styles.titleBar}>
        <View style={styles.dot} />
        <View style={[styles.dot, { background: '#f9ca24' }]} />
        <View style={[styles.dot, { background: '#00b894' }]} />
        <Text style={styles.titleText}>Terminal</Text>
      </View>
      <ScrollView
        ref={scrollRef}
        style={styles.output}
        contentContainerStyle={styles.outputContent}
      >
        {output.length === 0 ? (
          <Text style={styles.empty}>Waiting for output...</Text>
        ) : (
          output.map((line, i) => (
            <Text key={i} style={[styles.line, { color: colorize(line) }]}>
              {line}
            </Text>
          ))
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    height: 250, backgroundColor: '#050508', borderTopWidth: 1,
    borderTopColor: '#1a1a2e',
  },
  titleBar: {
    flexDirection: 'row', alignItems: 'center', padding: 8,
    backgroundColor: '#0a0a0f', borderBottomWidth: 1, borderBottomColor: '#1a1a2e',
  },
  dot: { width: 10, height: 10, borderRadius: 5, background: '#ff6b6b', marginRight: 6 },
  titleText: { fontSize: 11, color: '#666', marginLeft: 4 },
  output: { flex: 1 },
  outputContent: { padding: 10 },
  empty: { color: '#444', fontStyle: 'italic' },
  line: { fontSize: 11, fontFamily: 'monospace', lineHeight: 16 },
});
