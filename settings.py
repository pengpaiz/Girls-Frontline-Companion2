"""设置模块 — json 持久化（置顶、窗口位置）"""
import json
import os

CONFIG_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'AuraPet')
SETTINGS_PATH = os.path.join(CONFIG_DIR, 'settings.json')


def _read():
    try:
        with open(SETTINGS_PATH, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _write(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load():
    """读取设置，缺省用默认值"""
    d = _read()
    return {
        'topmost': bool(d.get('topmost', True)),
        'pos': d.get('pos'),
    }


def save(**kwargs):
    """增量保存设置"""
    d = _read()
    d.update(kwargs)
    _write(d)
