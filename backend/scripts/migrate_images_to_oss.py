"""将普通上传图片迁移到 OSS，分阶段校验、改引用、清理；备份仅含元数据。"""
import argparse
import hashlib
import json
import mimetypes
import re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen
from sqlalchemy import MetaData, String, JSON, select, update, and_
from backend.app.core.config import settings
from backend.app.core.database import engine
from backend.app.core.cache import invalidate_article_list_cache
from backend.app.services.object_storage import put_object, storage_enabled
from backend.app.services.site_settings import SETTINGS_PATH


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rewrite(value, mapping):
    if isinstance(value, dict):
        return {k: rewrite(v, mapping) for k, v in value.items()}
    if isinstance(value, list):
        return [rewrite(v, mapping) for v in value]
    if not isinstance(value, str):
        return value
    hosts = {'www.ranjl.cn', 'ranjl.cn', '47.111.75.30', 'localhost', '127.0.0.1', urlsplit(settings.public_base_url).hostname}
    def replace(match):
        original = match.group()
        parsed = urlsplit(original)
        if parsed.hostname and parsed.hostname not in hosts:
            return original
        return mapping.get(parsed.path, original)
    return re.sub(r'https?://[^\s<>"\x27)]+|(?<![\w/:])/uploads/[\w./%-]+', replace, value)


def save(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    path.chmod(0o600)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'apply', 'delete'])
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    assert storage_enabled(), 'OSS must be enabled'
    root = settings.upload_path.resolve()
    if args.phase == 'prepare':
        assert not args.manifest.exists(), 'Manifest already exists'
        entries = []
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp', '.gif'}:
                continue
            assert not path.is_symlink()
            relative = path.resolve().relative_to(root).as_posix()
            content = path.read_bytes()
            key = f"{settings.oss_object_prefix.strip('/')}/uploads/{relative}"
            url = put_object(key, content, mimetypes.guess_type(path.name)[0])
            with urlopen(url, timeout=30) as response:
                assert response.headers.get_content_type().startswith('image/')
                assert digest(response.read()) == digest(content), relative
            entries.append({'relative':relative,'url':url,'sha256':digest(content),'size':len(content)})
            print('verified', relative, flush=True)
        save(args.manifest, {'root':str(root),'entries':entries})
        print('PREPARED', len(entries), sum(e['size'] for e in entries))
        return
    manifest = json.loads(args.manifest.read_text())
    assert manifest['root'] == str(root)
    mapping = {'/uploads/'+e['relative']:e['url'] for e in manifest['entries']}
    metadata = MetaData()
    metadata.reflect(engine)
    changes = []
    with engine.begin() as connection:
        for table in metadata.sorted_tables:
            columns = [c for c in table.c if isinstance(c.type, (String, JSON))]
            if not columns:
                continue
            for row in connection.execute(select(table).with_for_update()).mappings():
                new = {c.name:rewrite(row[c.name],mapping) for c in columns if rewrite(row[c.name],mapping) != row[c.name]}
                if not new:
                    continue
                assert args.phase != 'delete', f'References remain in {table.name}'
                pk = {c.name:row[c.name] for c in table.primary_key}
                assert pk
                changes.append({'table':table.name,'pk':pk,'before':{k:row[k] for k in new},'after':new})
        original = json.loads(SETTINGS_PATH.read_text())
        updated = rewrite(original, mapping)
        if args.phase == 'apply':
            backup = args.manifest.with_suffix('.references.json')
            assert not backup.exists(), 'Reference backup already exists'
            save(backup, {'database':changes,'settings':original})
            for change in changes:
                table = metadata.tables[change['table']]
                connection.execute(update(table).where(and_(*(table.c[k]==v for k,v in change['pk'].items()))).values(**change['after']))
            temporary = SETTINGS_PATH.with_suffix('.migration.tmp')
            temporary.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding='utf-8')
            temporary.replace(SETTINGS_PATH)
        else:
            assert original == updated, 'Settings references remain'
    if args.phase == 'apply':
        invalidate_article_list_cache()
        print('APPLIED',len(changes),'rows')
        return
    # 全量校验通过后才删除；仅清理清单中、哈希未变化且位于上传目录内的文件。
    for entry in manifest['entries']:
        path = (root / entry['relative']).resolve()
        path.relative_to(root)
        assert digest(path.read_bytes()) == entry['sha256']
        with urlopen(entry['url'], timeout=30) as response:
            assert digest(response.read()) == entry['sha256']
    for entry in manifest['entries']:
        path = (root / entry['relative']).resolve()
        assert digest(path.read_bytes()) == entry['sha256']
        path.unlink()
    print('DELETED',len(manifest['entries']))

if __name__ == '__main__':
    main()
