import copy
import importlib.util
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path
import tempfile
import unittest


HERE = Path(__file__).resolve().parents[1]
loader = SourceFileLoader('firefox_config', str(HERE / 'files/firefox-config'))
spec = importlib.util.spec_from_loader(loader.name, loader)
config = importlib.util.module_from_spec(spec)
loader.exec_module(config)
PROXY_PATH = ('policies', '3rdparty', 'Extensions', 'foxyproxy@eric.h.jung')


class PolicyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.manager = config.PolicyManager(self.root)
        self.template = json.loads((HERE / 'data/policies.json').read_text())
        self.presets = json.loads((HERE / 'data/foxyproxy-proxies.json').read_text())
        self.manager.template_path.parent.mkdir(parents=True)
        self.write_template(self.template)
        self.manager.proxies_path.write_text(json.dumps(self.presets))

    def write_template(self, value):
        self.manager.template_path.write_text(json.dumps(value))

    def legacy_install(self, original=None):
        if original is not None:
            self.manager.policy_path.parent.mkdir(parents=True, exist_ok=True)
            self.manager.policy_path.write_text(json.dumps(original))
        old = copy.deepcopy(self.template)
        config.put_path(old, PROXY_PATH, self.presets)
        self.write_template(old)
        self.manager.apply()
        self.write_template(self.template)

    def test_new_install_does_not_manage_foxyproxy(self):
        self.manager.apply()
        installed = self.manager.load_policy()
        self.assertIs(config.get_path(installed, PROXY_PATH), config.MISSING)
        self.assertIn('foxyproxy@eric.h.jung', installed['policies']['ExtensionSettings'])
        self.manager.check()

    def test_upgrade_removes_all_legacy_managed_proxy_values(self):
        self.legacy_install()
        self.manager.apply()
        installed = self.manager.load_policy()
        self.assertNotIn('3rdparty', installed['policies'])
        self.manager.check()
        backups = list((self.manager.state_directory / 'backups').glob('*.json'))
        self.assertTrue(backups)
        self.assertTrue(any(config.get_path(json.loads(p.read_text()), PROXY_PATH) == self.presets for p in backups))

    def test_upgrade_preserves_other_policies_and_profile_storage(self):
        original = {'policies': {'Homepage': {'URL': 'https://example.test/'},
                                '3rdparty': {'Extensions': {'other@example.test': {'custom': True}}}}}
        profile = self.root / 'home/user/.mozilla/firefox/profile/storage.js'
        profile.parent.mkdir(parents=True)
        profile.write_bytes(b'user proxy settings')
        self.legacy_install(original)
        self.manager.apply()
        installed = self.manager.load_policy()
        self.assertEqual(installed['policies']['Homepage'], original['policies']['Homepage'])
        self.assertEqual(installed['policies']['3rdparty'], original['policies']['3rdparty'])
        self.assertEqual(profile.read_bytes(), b'user proxy settings')
        self.manager.check()

    def test_admin_modified_proxy_policy_is_preserved_and_reported(self):
        self.legacy_install()
        installed = self.manager.load_policy()
        config.put_path(installed, (*PROXY_PATH, 'mode'), 'custom-admin-mode')
        self.manager.policy_path.write_text(json.dumps(installed))
        self.manager.apply()
        self.assertEqual(config.get_path(self.manager.load_policy(), (*PROXY_PATH, 'mode')), 'custom-admin-mode')
        with self.assertRaisesRegex(ValueError, 'administrator-managed'):
            self.manager.check()

    def test_reapply_is_idempotent_and_remove_restores_original(self):
        original = {'policies': {'Homepage': {'URL': 'https://example.test/'}}}
        self.legacy_install(original)
        self.manager.apply()
        before = self.manager.policy_path.read_bytes()
        self.manager.apply()
        self.assertEqual(self.manager.policy_path.read_bytes(), before)
        self.manager.remove()
        self.assertEqual(self.manager.load_policy(), original)

    def test_missing_ownership_state_does_not_delete_existing_policy(self):
        self.legacy_install()
        self.manager.state_path.unlink()
        self.manager.apply()
        self.assertEqual(config.get_path(self.manager.load_policy(), PROXY_PATH), self.presets)
        with self.assertRaisesRegex(ValueError, 'administrator-managed'):
            self.manager.check()

    def test_import_presets_have_expected_endpoints(self):
        self.assertEqual(self.presets['mode'], 'disable')
        proxies = {entry['title']: entry for entry in self.presets['data']}
        for title, port, kind in [('Burp Suite', '8080', 'http'), ('SOCKS5', '1080', 'socks5')]:
            self.assertEqual(proxies[title]['hostname'], '127.0.0.1')
            self.assertEqual(proxies[title]['port'], port)
            self.assertEqual(proxies[title]['type'], kind)


if __name__ == '__main__':
    unittest.main()
