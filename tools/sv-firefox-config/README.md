# Firefox proxy configuration

Version 0.1.7 removes Svent's managed FoxyProxy settings. Managed storage is
mandatory configuration: FoxyProxy displays its options but does not apply user
changes while that storage is active. Enforcing `mode: disable` prevented users
from selecting Burp Suite normally.

The package still installs Firefox privacy policies and extensions. It does not
write to Firefox profiles or extension databases. On upgrade, the existing
policy ownership journal removes unchanged values owned by the previous Svent
package. Unrelated policies and administrator changes are preserved. Restart
Firefox completely after upgrading to reload policies and FoxyProxy.

## Editable proxy presets

Open FoxyProxy Options, find Settings: Import/Export, and import:

```text
/usr/share/svent/firefox/foxyproxy-proxies.json
```

Click Save, then select Burp Suite or SOCKS5 from the extension popup. Import is
optional and performed once per Firefox profile. The package does not force an
import or overwrite custom proxies. Review the imported settings before saving
if you already use FoxyProxy: the preset file includes the initially disabled
mode and other defaults. After saving, the extension controls these settings.

Presets are Burp Suite at `127.0.0.1:8080` using HTTP and SOCKS5 at
`127.0.0.1:1080`. The corresponding proxy must be running. HTTPS interception
requires separately configuring the appropriate lab certificate trust.

The JSON file may contain `mode: disable` because it is an editable import
template, not an enforced policy. Removing only that field from a managed policy
would not make managed settings editable.

## Checks and migration

```bash
/usr/libexec/svent/firefox-config --check
/usr/libexec/svent/firefox-config --status
```

If a separate administrator policy still manages FoxyProxy, the check reports it
instead of claiming that proxy selection is unlocked. Inspect `about:policies`
and the policy source. The package does not delete settings it does not own.
Without the old ownership journal, an existing managed policy cannot safely be
attributed to Svent; review and remove that policy manually after a backup.

## Build and release

```bash
python3 -m unittest discover -s tests -v
dpkg-checkbuilddeps
dpkg-buildpackage -b -us -uc
```

Build only `sv-firefox-config` 0.1.7. The Web metapackage does not need rebuilding
because its dependencies are unchanged. Preserve the tested `.deb`, test the
upgrade in a Debian 13 VM, and use `svent-bin/SVENT-MAINTENANCE.md` to import it
into the complete recovered repository and publish through the existing
publisher. Do not replace an already published package under the same version.

Source and migration tests do not replace a Firefox UI test. On the test VM,
verify that the managed FoxyProxy policy is absent, import the presets, select
Burp, switch to Disabled and SOCKS5, and restart Firefox to confirm the user
selection is retained. Existing custom proxies should remain available.

FoxyProxy's behavior and import workflow are documented at:

https://foxyproxy.github.io/browser-extension/src/content/help.html
