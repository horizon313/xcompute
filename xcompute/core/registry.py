"""Plugin registry + capability graph.

A plugin is a folder with manifest.json:
{"name": "cpu_backend", "version": "0.1.0",
 "provides": ["backend.cpu"], "requires": [],
 "entry": "plugin:CpuBackend"}
Missing dependencies never crash the core: the plugin is just skipped.
"""
import importlib.util
import json
import os
import sys


class Registry:
    def __init__(self):
        self.manifests = {}   # name -> manifest
        self.enabled = {}     # name -> bool
        self.instances = {}   # name -> plugin instance
        self.skipped = {}     # name -> reason

    def scan(self, plugins_dir):
        for d in sorted(os.listdir(plugins_dir)):
            path = os.path.join(plugins_dir, d, "manifest.json")
            if not os.path.isfile(path):
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    m = json.load(f)
                self.manifests[m["name"]] = dict(m, _dir=os.path.join(plugins_dir, d))
            except (OSError, ValueError, KeyError) as e:
                self.skipped[d] = "bad manifest: %s" % e
        self._resolve()

    def capabilities(self):
        """Capability graph: capability -> [plugin names] (enabled only)."""
        graph = {}
        for name, m in self.manifests.items():
            if self.enabled.get(name):
                for cap in m.get("provides", []):
                    graph.setdefault(cap, []).append(name)
        return graph

    def _resolve(self):
        for name in self.manifests:
            self.enabled.setdefault(name, False)
        changed = True
        while changed:
            changed = False
            for name, m in self.manifests.items():
                if self.enabled[name]:
                    continue
                caps = set(self.capabilities())
                if all(r in caps for r in m.get("requires", [])):
                    self.enabled[name] = True
                    self.skipped.pop(name, None)
                    changed = True
        caps = set(self.capabilities())
        for name, m in self.manifests.items():
            if not self.enabled[name]:
                self.skipped[name] = "missing: " + ", ".join(
                    r for r in m.get("requires", []) if r not in caps)

    def disable(self, name):
        self.enabled[name] = False
        self.instances.pop(name, None)
        changed = True  # cascade to dependents
        while changed:
            changed = False
            caps = set(self.capabilities())
            for n, m in self.manifests.items():
                if self.enabled.get(n) and not all(r in caps for r in m.get("requires", [])):
                    self.enabled[n] = False
                    self.instances.pop(n, None)
                    changed = True
                    caps = set(self.capabilities())

    def load(self, name):
        """Instantiate a plugin. Any failure disables it, never the core."""
        m = self.manifests[name]
        try:
            mod_name, cls_name = m["entry"].split(":")
            file = os.path.join(m["_dir"], mod_name + ".py")
            spec = importlib.util.spec_from_file_location("xc_plugin_" + name, file)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            self.instances[name] = getattr(mod, cls_name)()
            return self.instances[name]
        except Exception as e:  # isolate plugin failures
            self.enabled[name] = False
            self.skipped[name] = "load failed: %s" % e
            return None
