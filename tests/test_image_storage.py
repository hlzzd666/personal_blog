import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.services.auth import require_admin_session
from backend.app.services.object_storage import ObjectStorageError

class ImageStorageTest(unittest.TestCase):
    def test_upload_storage_and_errors(self):
        with TemporaryDirectory() as directory, patch.object(settings, 'upload_dir', directory), patch.object(settings, 'media_storage_driver', 'oss'), patch('backend.app.services.media.put_object') as put:
            app.dependency_overrides[require_admin_session] = lambda: 'admin'
            self.addCleanup(app.dependency_overrides.pop, require_admin_session)
            client = TestClient(app)
            put.return_value = 'https://cdn.example.test/uploads/image.png'
            result = client.post('/api/v1/media/images', files={'file': ('test.png', b'image-content', 'image/png')})
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()['data']['url'], put.return_value)
            self.assertEqual(put.call_args.args[1:], (b'image-content', 'image/png'))
            self.assertEqual(list(Path(directory).iterdir()), [])
            put.side_effect = ObjectStorageError('failed')
            self.assertEqual(client.post('/api/v1/media/images', files={'file': ('x.png', b'x', 'image/png')}).status_code, 502)
            self.assertEqual(list(Path(directory).iterdir()), [])
            put.reset_mock()
            self.assertEqual(client.post('/api/v1/media/images', files={'file': ('x.png', b'', 'image/png')}).status_code, 422)
            self.assertEqual(client.post('/api/v1/media/images', files={'file': ('x.png', b'x' * (10*1024*1024+1), 'image/png')}).status_code, 413)
            put.assert_not_called()
            with patch.object(settings, 'media_storage_driver', 'local'):
                self.assertEqual(client.post('/api/v1/media/images', files={'file': ('x.png', b'x', 'image/png')}).status_code, 200)
                self.assertEqual(len(list(Path(directory).iterdir())), 1)


class ImageMigrationTest(unittest.TestCase):
    def test_only_local_references_are_rewritten(self):
        from backend.scripts.migrate_images_to_oss import rewrite
        mapping = {'/uploads/a.webp': 'https://cdn.example.test/prod/uploads/a.webp'}
        source = {'body': '![图](/uploads/a.webp) <img src="https://www.ranjl.cn/uploads/a.webp">', 'external': 'https://other.example/uploads/a.webp'}
        result = rewrite(source, mapping)
        self.assertEqual(result['body'].count(mapping['/uploads/a.webp']), 2)
        self.assertEqual(result['external'], source['external'])
        self.assertEqual(rewrite(result, mapping), result)

if __name__ == '__main__':
    unittest.main()
