package com.cyberlab;

import android.content.Context;
import android.content.res.AssetManager;
import android.util.Log;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import com.facebook.react.bridge.Arguments;
import com.facebook.react.bridge.Promise;
import com.facebook.react.bridge.ReactApplicationContext;
import com.facebook.react.bridge.ReactContextBaseJavaModule;
import com.facebook.react.bridge.ReactMethod;
import com.facebook.react.bridge.ReadableMap;
import com.facebook.react.bridge.WritableMap;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * BinaryExecutor — runs pre-compiled ARM64 binaries directly from APK assets.
 * No Python wrapper needed for native tools (nmap, aircrack, john, etc.)
 * Python tools (sqlmap, nikto, routersploit) run via Chaquopy.
 */
public class BinaryExecutor extends ReactContextBaseJavaModule {
    private static final String TAG = "BinaryExecutor";
    private final ReactApplicationContext reactContext;
    private final ExecutorService executor;
    private String basePath;
    private String binariesPath;

    public BinaryExecutor(ReactApplicationContext context) {
        super(context);
        this.reactContext = context;
        this.executor = Executors.newCachedThreadPool();
        initPaths();
    }

    @Override
    public String getName() {
        return "BinaryExecutor";
    }

    private void initPaths() {
        basePath = reactContext.getFilesDir().getAbsolutePath();
        binariesPath = basePath + "/assets/binaries";
    }

    /**
     * Execute a native binary directly with arguments.
     * The binary is extracted from APK assets to internal storage on first run,
     * then executed via ProcessBuilder.
     */
    @ReactMethod
    public void executeNative(String toolName, ReadableMap args, Promise promise) {
        executor.execute(() -> {
            try {
                // Ensure binary is extracted and executable
                String binaryPath = extractAndPrepareBinary(toolName);
                if (binaryPath == null) {
                    promise.resolve(createErrorResult("Binary not found: " + toolName));
                    return;
                }

                // Build command
                java.util.List<String> command = new java.util.ArrayList<>();
                command.add(binaryPath);

                // Add tool-specific arguments
                if (args != null) {
                    addToolArgs(toolName, args, command);
                }

                // Execute
                ProcessBuilder pb = new ProcessBuilder(command);
                pb.redirectErrorStream(true);
                pb.directory(new File(basePath));

                Process process = pb.start();

                // Read output
                java.io.BufferedReader reader = new java.io.BufferedReader(
                    new java.io.InputStreamReader(process.getInputStream())
                );
                StringBuilder output = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    output.append(line).append("\n");
                }

                int exitCode = process.waitFor();
                reader.close();

                WritableMap result = Arguments.createMap();
                result.putBoolean("success", exitCode == 0);
                result.putInt("exitCode", exitCode);
                result.putString("output", output.toString());
                result.putString("tool", toolName);
                promise.resolve(result);

            } catch (Exception e) {
                Log.e(TAG, "executeNative error: " + e.getMessage(), e);
                promise.resolve(createErrorResult(e.getMessage()));
            }
        });
    }

    /**
     * Check if a binary exists (either extracted or in APK assets).
     */
    public boolean hasBinary(String toolName) {
        File f = new File(binariesPath + "/" + toolName);
        if (f.exists() && f.canExecute()) return true;
        try {
            reactContext.getAssets().open("binaries/" + toolName).close();
            return true;
        } catch (Exception) {
            return false;
        }
    }

    /**
     * Extract binary from APK assets to internal storage and set executable.
     * Handles both raw binaries and .jar files.
     */
    private String extractAndPrepareBinary(String toolName) {
        // Handle .jar files (apktool, etc.)
        if (toolName.endsWith(".jar")) {
            return extractJar(toolName);
        }

        String binaryFile = binariesPath + "/" + toolName;
        File f = new File(binaryFile);

        if (f.exists() && f.canExecute()) {
            return binaryFile;
        }

        try {
            // Ensure directory exists
            f.getParentFile().mkdirs();

            // Copy from assets
            AssetManager am = reactContext.getAssets();
            InputStream is = am.open("binaries/" + toolName);
            OutputStream os = new FileOutputStream(f);

            byte[] buffer = new byte[8192];
            int len;
            while ((len = is.read(buffer)) > 0) {
                os.write(buffer, 0, len);
            }
            is.close();
            os.close();

            // Set executable permissions
            f.setExecutable(true, false);
            f.setReadable(true, false);

            Log.i(TAG, "Extracted binary: " + binaryFile);
            return binaryFile;

        } catch (Exception e) {
            Log.e(TAG, "Failed to extract binary " + toolName + ": " + e.getMessage());
            return null;
        }
    }

    /**
     * Extract a JAR file (for apktool, etc.)
     */
    private String extractJar(String jarName) {
        String jarPath = binariesPath + "/" + jarName;
        File f = new File(jarPath);

        if (f.exists()) return jarPath;

        try {
            f.getParentFile().mkdirs();
            AssetManager am = reactContext.getAssets();
            InputStream is = am.open("binaries/" + jarName);
            OutputStream os = new FileOutputStream(f);

            byte[] buffer = new byte[8192];
            int len;
            while ((len = is.read(buffer)) > 0) {
                os.write(buffer, 0, len);
            }
            is.close();
            os.close();

            Log.i(TAG, "Extracted JAR: " + jarPath);
            return jarPath;
        } catch (Exception e) {
            Log.e(TAG, "Failed to extract JAR " + jarName + ": " + e.getMessage());
            return null;
        }
    }

    /**
     * Add tool-specific arguments to the command.
     * Each tool has its own argument mapping.
     */
    private void addToolArgs(String toolName, ReadableMap args, java.util.List<String> command) {
        switch (toolName) {
            case "nmap":
                addNmapArgs(args, command);
                break;
            case "aircrack-ng":
                addAircrackArgs(args, command);
                break;
            case "john":
                addJohnArgs(args, command);
                break;
            case "hashcat":
                addHashcatArgs(args, command);
                break;
            case "hydra":
                addHydraArgs(args, command);
                break;
            case "tcpdump":
                addTcpdumpArgs(args, command);
                break;
            case "masscan":
                addMasscanArgs(args, command);
                break;
            case "reaver":
                addReaverArgs(args, command);
                break;
            case "cameradar":
                addCameradarArgs(args, command);
                break;
            case "gobuster":
                addGobusterArgs(args, command);
                break;
            case "ffuf":
                addFfufArgs(args, command);
                break;
            case "apktool":
                addApktoolArgs(args, command);
                break;
            default:
                // Generic: add all string args as --key value
                addGenericArgs(args, command);
                break;
        }
    }

    private void addNmapArgs(ReadableMap args, java.util.List<String> cmd) {
        if (args.hasKey("target")) cmd.add(args.getString("target"));
        if (args.hasKey("ports")) cmd.add("-p " + args.getString("ports"));
        if (args.hasKey("scanType")) {
            switch (args.getString("scanType")) {
                case "quick": cmd.add("-sV -sC"); break;
                case "full": cmd.add("-sV -sC -A -p-"); break;
                case "udp": cmd.add("-sU"); break;
                case "stealth": cmd.add("-sS"); break;
                case "vuln": cmd.add("--script=vuln"); break;
            }
        }
        if (args.hasKey("osDetect")) cmd.add("-O");
        if (args.hasKey("timing")) cmd.add("-T" + args.getString("timing"));
        if (args.hasKey("script")) cmd.add("--script=" + args.getString("script"));
    }

    private void addAircrackArgs(ReadableMap args, java.util.List<String> cmd) {
        if (args.hasKey("captureFile")) cmd.add(args.getString("captureFile"));
        if (args.hasKey("wordlist")) cmd.add("-w " + resolveWordlist(args.getString("wordlist")));
    }

    private void addJohnArgs(ReadableMap args, java.util.List<String> cmd) {
        if (args.hasKey("hashFile")) cmd.add(args.getString("hashFile"));
        if (args.hasKey("wordlist")) cmd.add("--wordlist=" + resolveWordlist(args.getString("wordlist")));
        if (args.hasKey("format")) cmd.add("--format=" + args.getString("format"));
        if (args.hasKey("rules")) cmd.add("--rules");
    }

    private void addHashcatArgs(ReadableMap args, java.util.List<String> cmd) {
        if (args.hasKey("mode")) cmd.add("-m " + args.getString("mode"));
        else cmd.add("-m 22000");
        cmd.add("-a 0");
        if (args.hasKey("hashFile")) cmd.add(args.getString("hashFile"));
        if (args.hasKey("wordlist")) cmd.add(resolveWordlist(args.getString("wordlist")));
        cmd.add("--force");
        cmd.add("-O");
    }

    private void addHydraArgs(ReadableMap args, java.util.List<String> cmd) {
        if (args.hasKey("username")) cmd.add("-l " + args.getString("username"));
        if (args.hasKey("userlist")) cmd.add("-L " + resolveWordlist(args.getString("userlist")));
        if (args.hasKey("password")) cmd.add("-p " + args.getString("password"));
        if (args.hasKey("passlist")) cmd.add("-P " + resolveWordlist(args.getString("passlist")));
        if (args.hasKey("service")) cmd.add(args.getString("service"));
        if (args.hasKey("target")) cmd.add(args.getString("target"));
    }

    private void addTcpdumpArgs(ReadableMap args, java.util.List<String> cmd) {
        if (args.hasKey("interface")) cmd.add("-i " + args.getString("interface"));
        else cmd.add("-i wlan0");
        if (args.hasKey("count")) cmd.add("-c " + args.getString("count"));
        if (args.hasKey("filter")) cmd.add(args.getString("filter"));
        if (args.hasKey("outputFile")) {
            cmd.add("-w " + args.getString("outputFile"));
        } else {
            cmd.add("-w " + basePath + "/capture.pcap");
        }
    }

    private void addMasscanArgs(ReadableMap args, java.util.List<String> cmd) {
        if (args.hasKey("target")) cmd.add(args.getString("target"));
        if (args.hasKey("ports")) cmd.add("-p " + args.getString("ports"));
        else cmd.add("-p 1-65535");
        if (args.hasKey("rate")) cmd.add("--rate=" + args.getString("rate"));
    }

    private void addReaverArgs(ReadableMap args, java.util.List<String> cmd) {
        if (args.hasKey("interface")) cmd.add("-i " + args.getString("interface"));
        else cmd.add("-i wlan0");
        if (args.hasKey("bssid")) cmd.add("-b " + args.getString("bssid"));
        if (args.hasKey("verbose")) cmd.add("-vv");
    }

    private void addCameradarArgs(ReadableMap args, java.util.List<String> cmd) {
        if (args.hasKey("target")) cmd.add("-t " + args.getString("target"));
        if (args.hasKey("port")) cmd.add("-p " + args.getString("port"));
        if (args.hasKey("timeout")) cmd.add("--timeout " + args.getString("timeout"));
    }

    private void addGobusterArgs(ReadableMap args, java.util.List<String> cmd) {
        cmd.add("dir");
        if (args.hasKey("target")) cmd.add("-u " + args.getString("target"));
        if (args.hasKey("wordlist")) cmd.add("-w " + resolveWordlist(args.getString("wordlist")));
        if (args.hasKey("extensions")) cmd.add("-x " + args.getString("extensions"));
    }

    private void addFfufArgs(ReadableMap args, java.util.List<String> cmd) {
        if (args.hasKey("target")) cmd.add("-u " + args.getString("target") + "/FUZZ");
        if (args.hasKey("wordlist")) cmd.add("-w " + resolveWordlist(args.getString("wordlist")));
        if (args.hasKey("threads")) cmd.add("-t " + args.getString("threads"));
    }

    private void addApktoolArgs(ReadableMap args, java.util.List<String> cmd) {
        if (args.hasKey("action")) cmd.add(args.getString("action"));
        else cmd.add("d");
        if (args.hasKey("input")) cmd.add(args.getString("input"));
        if (args.hasKey("output")) cmd.add("-o " + args.getString("output"));
        cmd.add("-f");
    }

    private void addGenericArgs(ReadableMap args, java.util.List<String> cmd) {
        com.facebook.react.bridge.ReadableMapKeySetIterator it = args.keySetIterator();
        while (it.hasNextKey()) {
            String key = it.nextKey();
            String val = args.getString(key);
            if (val != null && !val.isEmpty()) {
                cmd.add("--" + key);
                cmd.add(val);
            }
        }
    }

    private String resolveWordlist(String name) {
        String wlPath = basePath + "/assets/wordlists/" + name;
        if (new File(wlPath).exists()) {
            return wlPath;
        }
        return name;
    }

    private WritableMap createErrorResult(String error) {
        WritableMap result = Arguments.createMap();
        result.putBoolean("success", false);
        result.putString("error", error);
        return result;
    }
}
