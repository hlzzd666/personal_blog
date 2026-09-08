"""Generate the two approved gallery references; credentials remain in memory."""
import getpass
import os
from pathlib import Path
import subprocess
import sys
import requests

ROOT = Path(__file__).resolve().parents[2]
SKILL = Path.home() / '.codex/skills/image2-api/scripts'

def main():
    env = os.environ.copy()
    env['IMAGE_API_KEY'] = env.get('IMAGE_API_KEY') or getpass.getpass('Image API key: ')
    env['IMAGE_API_BASE_URL'] = 'https://suoxie.codes/v1'
    env['IMAGE_API_MODEL'] = 'gpt-image-2'
    env['IMAGE_API_MODEL_FAMILY'] = 'gpt-image-2'
    env.pop('IMAGE_API_PROVIDERS', None)
    response = requests.get(env['IMAGE_API_BASE_URL'] + '/models', headers={'Authorization': 'Bearer ' + env['IMAGE_API_KEY']}, timeout=45)
    response.raise_for_status()
    models = [m['id'] for m in response.json().get('data', [])]
    if 'gpt-image-2' not in models:
        raise RuntimeError('The relay does not list gpt-image-2')
    print('Relay model verified: gpt-image-2', flush=True)
    materials = '--materials' in sys.argv
    for name in (('teak', 'walnut') if materials else ('perspective', 'plan')):
        args = [sys.executable, str(SKILL / ('edit_image.py' if materials else 'generate_image.py')), '--prompt-file', str(ROOT / 'docs/gallery-design' / (name + '.txt')), '--model', 'gpt-image-2', '--model-family', 'gpt-image-2', '--size', '1024x1024', '--quality', 'high' if materials or name == 'plan' else 'medium', '--count', '1', '--name', name, '--output-dir', str(ROOT / 'artifacts/gallery/reference' / name), '--timeout', '300', '--max-retries', '1', '--json']
        if materials:
            args += ['--image', str(ROOT / 'artifacts/gallery/reference/perspective/perspective.png')]
        subprocess.run(args + ['--dry-run'], env=env, check=True)
        subprocess.run(args, env=env, check=True)

if __name__ == '__main__':
    main()
