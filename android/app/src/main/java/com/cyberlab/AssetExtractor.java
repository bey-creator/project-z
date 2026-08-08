package com.cyberlab;

import android.content.Context;
import android.content.res.AssetManager;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.IOException;

/**
 * Extracts APK assets (binaries, python, wordlists, templates) to internal storage
 * so Chaquopy can access them at runtime.
 */
public class AssetExtractor {
    private static final String TAG = "CyberLabAssets";

    public static void extractAll(Context context, String basePath, String[] assetNames) {
        AssetManager am = context.getAssets();
        for (String name : assetNames) {
            try {
                extractRecursive(am, name, basePath + "/assets/" + name);
            } catch (Exception e) {
                Log.e(TAG, "Failed to extract " + name + ": " + e.getMessage());
            }
        }
    }

    private static void extractRecursive(AssetManager am, String assetPath, String destPath) throws IOException {
        String[] list = am.list(assetPath);
        if (list == null || list.length == 0) {
            // It's a file
            extractFile(am, assetPath, destPath);
        } else {
            // It's a directory
            File dir = new File(destPath);
            if (!dir.exists()) dir.mkdirs();
            for (String child : list) {
                extractRecursive(am, assetPath + "/" + child, destPath + "/" + child);
            }
        }
    }

    private static void extractFile(AssetManager am, String assetPath, String destPath) {
        try {
            File destFile = new File(destPath);
            if (destFile.exists() && destFile.length() > 0) return; // Skip if already extracted

            destFile.getParentFile().mkdirs();
            InputStream is = am.open(assetPath);
            FileOutputStream os = new FileOutputStream(destPath);
            byte[] buffer = new byte[8192];
            int len;
            while ((len = is.read(buffer)) > 0) {
                os.write(buffer, 0, len);
            }
            os.close();
            is.close();

            // Set executable permission for binaries
            if (destPath.contains("/binaries/")) {
                destFile.setExecutable(true, false);
                destFile.setReadable(true, false);
            }
        } catch (Exception e) {
            Log.e(TAG, "Extract failed for " + assetPath + ": " + e.getMessage());
        }
    }
}
