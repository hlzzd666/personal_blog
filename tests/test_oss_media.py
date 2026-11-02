import unittest
from unittest.mock import patch, Mock
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from pathlib import Path
from backend.app.core.config import settings
from backend.app.services import media, object_storage

class OssMediaTest(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        for name,value in [('upload_dir',self.tmp.name),('media_storage_driver','oss'),('oss_object_prefix','blog/prod'),('oss_public_base_url','https://cdn.test')]:
            p=patch.object(settings,name,value);p.start();self.addCleanup(p.stop)
        self.key='blog/prod/uploads/'+'a'*32+'.webp'
        self.url=object_storage.public_url(self.key)
        p=patch.object(media,'_collect_reference_candidates',return_value=[media.MediaReferenceCandidate('文章','正文',f'![图]({self.url})')]);p.start();self.addCleanup(p.stop)

    def test_inventory_reference_and_storage_cleanup(self):
        local=Path(self.tmp.name)/'unused.png';local.write_bytes(b'x')
        other='blog/prod/uploads/'+'b'*32+'.webp'
        objects=[SimpleNamespace(key=key,size=2,last_modified=1) for key in [self.key,other,'blog/prod/model.glb']]
        with patch.object(media,'list_objects',return_value=objects),patch.object(media,'delete_object') as delete:
            result=media.list_media_files(Mock())
            self.assertEqual(result.total,4)
            self.assertTrue(next(i for i in result.items if i.url==self.url).referenced)
            media.cleanup_unreferenced_media_files(Mock(),'oss')
            delete.assert_called_once_with(other)
            self.assertTrue(local.exists())

    def test_permission_failure_shows_known_refs_but_blocks_cleanup(self):
        with patch.object(media,'list_objects',side_effect=object_storage.ObjectStorageError('permission')),patch.object(media,'delete_object') as delete:
            result=media.list_media_files(Mock())
            self.assertFalse(result.oss_complete)
            self.assertEqual(result.items[0].url,self.url)
            self.assertIsNone(result.items[0].size)
            with self.assertRaises(object_storage.ObjectStorageError):media.cleanup_unreferenced_media_files(Mock(),'oss')
            delete.assert_not_called()

    def test_pagination_and_prefix_guard(self):
        bucket=Mock()
        bucket.list_objects.side_effect=[SimpleNamespace(object_list=[SimpleNamespace(key=self.key)],is_truncated=True,next_marker='next'),SimpleNamespace(object_list=[],is_truncated=False)]
        with patch.object(object_storage,'_bucket',return_value=bucket):
            self.assertEqual(len(object_storage.list_objects()),1)
            self.assertEqual(bucket.list_objects.call_args.kwargs,{'prefix':'blog/prod/','marker':'next','max_keys':1000})
            with self.assertRaises(object_storage.ObjectStorageError):object_storage.delete_object('other/file.jpg')
            bucket.delete_object.assert_not_called()

if __name__=='__main__':unittest.main()
