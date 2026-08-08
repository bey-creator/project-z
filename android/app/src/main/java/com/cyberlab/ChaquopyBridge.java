package com.cyberlab;

import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import com.facebook.react.bridge.Arguments;
import com.facebook.react.bridge.Promise;
import com.facebook.react.bridge.ReactApplicationContext;
import com.facebook.react.bridge.ReactContextBaseJavaModule;
import com.facebook.react.bridge.ReactMethod;
import com.facebook.react.bridge.WritableMap;

import java.io.File;

/**
 * Chaquopy Bridge — connects React Native to the embedded Python runtime.
 * Python core modules are stored in assets/python/ and executed via Chaquopy.
 */
public class ChaquopyBridge extends ReactContextBaseJavaModule {
    private static final String TAG = "CyberLabBridge";
    private final ReactApplicationContext reactContext;
    private Python python;
    private PyObject bridgeModule;
    private boolean initialized = false;

    public ChaquopyBridge(ReactApplicationContext context) {
        super(context);
        this.reactContext = context;
        initPython();
    }

    @Override
    public String getName() {
        return "ChaquopyBridge";
    }

    private void initPython() {
        try {
            if (!Python.isStarted()) {
                Python.start(new AndroidPlatform(reactContext));
            }
            python = Python.getInstance();

            // Set up base directory for Python modules
            File baseDir = reactContext.getFilesDir();
            String basePath = baseDir.getAbsolutePath();

            // Extract assets to files dir (binaries, python, wordlists)
            extractAssets(basePath);

            // Set environment variable for Python code to find its files
            System.setProperty("CYBERLAB_BASE_DIR", basePath);

            // Add python path
            PyObject sys = python.getModule("sys");
            PyObject path = sys.get("path");
            path.callAttr("append", basePath + "/assets/python");

            // Load the core bridge module
            bridgeModule = python.getModule("core_bridge");
            initialized = true;
            Log.i(TAG, "Python bridge initialized at " + basePath);
        } catch (Exception e) {
            Log.e(TAG, "Failed to init Python: " + e.getMessage(), e);
            initialized = false;
        }
    }

    private void extractAssets(String basePath) {
        try {
            String[] assets = {"python", "binaries", "wordlists", "templates", "tools_manifest.json"};
            AssetExtractor.extractAll(reactContext, basePath, assets);
        } catch (Exception e) {
            Log.e(TAG, "Asset extraction failed: " + e.getMessage(), e);
        }
    }

    @ReactMethod
    public void getStatus(Promise promise) {
        try {
            if (!initialized || bridgeModule == null) {
                promise.resolve(createStatusError("Python not initialized"));
                return;
            }
            PyObject result = bridgeModule.callAttr("get_status");
            WritableMap map = PythonUtils.pyObjectToMap(result);
            promise.resolve(map);
        } catch (Exception e) {
            Log.e(TAG, "getStatus error: " + e.getMessage(), e);
            promise.resolve(createStatusError(e.getMessage()));
        }
    }

    @ReactMethod
    public void executeTool(String toolName, com.facebook.react.bridge.ReadableMap args, Promise promise) {
        try {
            if (!initialized || bridgeModule == null) {
                promise.resolve(createErrorResult("Python not initialized"));
                return;
            }
            PyObject argsDict = PythonUtils.readableMapToPyObject(python, args);
            PyObject result = bridgeModule.callAttr("execute_tool", toolName, argsDict);
            WritableMap map = PythonUtils.pyObjectToMap(result);
            promise.resolve(map);
        } catch (Exception e) {
            Log.e(TAG, "executeTool error: " + e.getMessage(), e);
            promise.resolve(createErrorResult(e.getMessage()));
        }
    }

    /**
     * Execute a Python-native tool via py_runner.
     * These are tools that are natively Python (sqlmap, nikto, routersploit, etc.)
     */
    @ReactMethod
    public void executePythonTool(String toolName, com.facebook.react.bridge.ReadableMap args, Promise promise) {
        try {
            if (!initialized) {
                promise.resolve(createErrorResult("Python not initialized"));
                return;
            }
            PyObject runnerModule = python.getModule("py_runner");
            PyObject argsDict = PythonUtils.readableMapToPyObject(python, args);
            PyObject result = runnerModule.callAttr("run_python_tool", toolName, argsDict);
            WritableMap map = PythonUtils.pyObjectToMap(result);
            promise.resolve(map);
        } catch (Exception e) {
            Log.e(TAG, "executePythonTool error: " + e.getMessage(), e);
            promise.resolve(createErrorResult(e.getMessage()));
        }
    }

    @ReactMethod
    public void getAvailableTools(Promise promise) {
        try {
            if (!initialized || bridgeModule == null) {
                promise.resolve(Arguments.createArray());
                return;
            }
            PyObject result = bridgeModule.callAttr("get_available_tools");
            promise.resolve(PythonUtils.pyObjectToArray(result));
        } catch (Exception e) {
            promise.resolve(Arguments.createArray());
        }
    }

    private WritableMap createStatusError(String error) {
        WritableMap map = Arguments.createMap();
        map.putString("error", error);
        map.putBoolean("rooted", false);
        map.putInt("total_tools", 0);
        map.putInt("available_tools", 0);
        return map;
    }

    private WritableMap createErrorResult(String error) {
        WritableMap map = Arguments.createMap();
        map.putBoolean("success", false);
        map.putString("error", error);
        return map;
    }
}
