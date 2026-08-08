package com.cyberlab;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;

import com.facebook.react.bridge.Arguments;
import com.facebook.react.bridge.ReadableMap;
import com.facebook.react.bridge.WritableArray;
import com.facebook.react.bridge.WritableMap;

import java.util.Iterator;
import java.util.Map;

/**
 * Utility class to convert between Python objects and React Native bridge types.
 */
public class PythonUtils {

    static WritableMap pyObjectToMap(PyObject obj) {
        WritableMap map = Arguments.createMap();
        if (obj == null) return map;
        try {
            for (Map.Entry<PyObject, PyObject> entry : obj.asMap().entrySet()) {
                String key = entry.getKey().toString();
                PyObject val = entry.getValue();
                if (val == null) continue;
                if (val.isString()) {
                    map.putString(key, val.toString());
                } else if (val.isInteger()) {
                    map.putInt(key, val.toInt());
                } else if (val.isLong()) {
                    map.putDouble(key, val.toLong());
                } else if (val.isFloat()) {
                    map.putDouble(key, val.toDouble());
                } else if (val.isBoolean()) {
                    map.putBoolean(key, val.toBoolean());
                } else if (val.isList()) {
                    WritableArray arr = Arguments.createArray();
                    for (PyObject item : val.asList()) {
                        if (item.isString()) arr.pushString(item.toString());
                        else if (item.isInteger()) arr.pushInt(item.toInt());
                        else if (item.isBoolean()) arr.pushBoolean(item.toBoolean());
                        else arr.pushString(item.toString());
                    }
                    map.putArray(key, arr);
                } else {
                    map.putString(key, val.toString());
                }
            }
        } catch (Exception e) {
            map.putString("_parse_error", e.getMessage());
        }
        return map;
    }

    static WritableArray pyObjectToArray(PyObject obj) {
        WritableArray arr = Arguments.createArray();
        if (obj == null) return arr;
        try {
            for (PyObject item : obj.asList()) {
                if (item.isDict()) {
                    arr.pushMap(pyObjectToMap(item));
                } else if (item.isString()) {
                    arr.pushString(item.toString());
                } else if (item.isInteger()) {
                    arr.pushInt(item.toInt());
                } else if (item.isBoolean()) {
                    arr.pushBoolean(item.toBoolean());
                } else {
                    arr.pushString(item.toString());
                }
            }
        } catch (Exception e) {
            // Return what we have
        }
        return arr;
    }

    static PyObject readableMapToPyObject(Python py, ReadableMap map) {
        PyObject dict = py.getBuiltins().callAttr("dict");
        if (map == null) return dict;
        Iterator<Map.Entry<String, Object>> it = map.getEntryIterator();
        while (it.hasNext()) {
            Map.Entry<String, Object> entry = it.next();
            String key = entry.getKey();
            Object val = entry.getValue();
            if (val instanceof String) {
                dict.callAttr("setdefault", key, (String) val);
            } else if (val instanceof Integer) {
                dict.callAttr("setdefault", key, ((Integer) val));
            } else if (val instanceof Boolean) {
                dict.callAttr("setdefault", key, ((Boolean) val));
            } else if (val instanceof Double) {
                dict.callAttr("setdefault", key, ((Double) val));
            } else if (val != null) {
                dict.callAttr("setdefault", key, val.toString());
            }
        }
        return dict;
    }
}
