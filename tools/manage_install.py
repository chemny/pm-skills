#!/usr/bin/env python3
"""Explicit local Skill installation. No downloads or implicit global targets."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import uuid
import zipfile

RECEIPT = '.pm-skills-install.json'
MANIFEST = 'release-manifest.json'
NAME = 'pm-skills'


class InstallError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def relative(value):
    p = PurePosixPath(value)
    if (not isinstance(value, str) or not value or '\\' in value or '\x00' in value
            or p.is_absolute() or str(p) != value
            or any(part in {'.', '..', '.git', '__pycache__'} for part in p.parts)
            or ':' in value):
        raise InstallError('unsafe-package-path')
    return value


def inventory(root, exclude=()):
    result = {}
    for p in sorted(Path(root).rglob('*')):
        if p.is_symlink():
            raise InstallError('symlinks-not-allowed')
        if p.is_file():
            rel = relative(p.relative_to(root).as_posix())
            if rel not in exclude:
                result[rel] = digest(p.read_bytes())
    return result


def verify(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise InstallError('package-directory-required')
    try:
        raw = (root / MANIFEST).read_bytes()
        manifest = json.loads(raw)
        meta = json.loads((root / 'release.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise InstallError('missing-or-invalid-release-manifest') from error
    files = manifest.get('files')
    if (manifest.get('schema_version') != 1 or not isinstance(files, dict)
            or not files or meta.get('name') != NAME
            or manifest.get('version') != meta.get('version')):
        raise InstallError('invalid-package-identity')
    for rel in files:
        relative(rel)
    if inventory(root, (RECEIPT, MANIFEST)) != files:
        raise InstallError('package-files-changed-or-unexpected')
    return {'name': NAME, 'version': meta['version'], 'manifest_sha256': digest(raw),
            'files': {**files, MANIFEST: digest(raw)}}


def compatible():
    if sys.platform != 'darwin':
        raise InstallError('this-release-supports-macos-only; no-files-changed')
    if sys.version_info[:2] < (3, 13):
        raise InstallError('Python-3.13-or-newer-required; no-runtime-installed')


def installed(target):
    identity = verify(target)
    try:
        receipt = json.loads((target / RECEIPT).read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise InstallError('unmanaged-installation-refused') from error
    if (receipt.get('name') != NAME or receipt.get('version') != identity['version']
            or receipt.get('files') != identity['files']
            or receipt.get('manifest_sha256') != identity['manifest_sha256']):
        raise InstallError('installation-receipt-mismatch')
    return identity


def target_path(skills_dir):
    base = Path(skills_dir).expanduser()
    if base.is_symlink():
        raise InstallError('symlink-install-root-refused')
    base = base.resolve()
    target = base / NAME
    if target.is_symlink():
        raise InstallError('symlink-installation-refused')
    return base, target


def backup(target, backup_dir):
    root = Path(backup_dir).expanduser().resolve()
    if root == target.parent or root.is_relative_to(target.parent):
        raise InstallError('backup-must-be-outside-skill-discovery-directory')
    root.mkdir(parents=True, exist_ok=True)
    file = root / (NAME + '-' + uuid.uuid4().hex + '.zip')
    with zipfile.ZipFile(file, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(target.rglob('*')):
            if p.is_file():
                archive.write(p, p.relative_to(target).as_posix())
    return str(file)


def replace_package(source, skills_dir, backup_dir=None, update=False):
    compatible()
    source = Path(source).resolve()
    identity = verify(source)
    base, target = target_path(skills_dir)
    if source == target or source.is_relative_to(target) or target.is_relative_to(source):
        raise InstallError('source-and-target-must-be-independent')
    if update:
        installed(target)
        if not backup_dir:
            raise InstallError('explicit-backup-directory-required')
        backup_root = Path(backup_dir).expanduser().resolve()
        if backup_root == base or backup_root.is_relative_to(base):
            raise InstallError('backup-must-be-outside-skill-discovery-directory')
    elif target.exists():
        raise InstallError('target-already-exists; no-overwrite')
    base.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.pm-install-', dir=base))
    old = None
    saved = None
    try:
        for rel in identity['files']:
            p = stage / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / rel, p)
        verify(stage)
        (stage / RECEIPT).write_text(json.dumps(identity, ensure_ascii=False, indent=2) + '\n')
        if update:
            # Recheck immediately before switching; leave local edits untouched.
            installed(target)
            saved = backup(target, backup_dir)
            old = base / ('.pm-retired-' + uuid.uuid4().hex)
            target.rename(old)
        try:
            stage.rename(target)
        except BaseException:
            if old is not None:
                old.rename(target)
            raise
        if old is not None:
            shutil.rmtree(old)  # verified task-owned old copy; ZIP backup already retained
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return {'action': 'update' if update else 'install', 'path': str(target),
            'version': identity['version'], 'manifest_sha256': identity['manifest_sha256'],
            'backup': saved, 'network_or_dependency_changes': False}


def uninstall(skills_dir, backup_dir):
    compatible()
    base, target = target_path(skills_dir)
    identity = installed(target)
    saved = backup(target, backup_dir)
    # Remove only an unchanged, receipt-owned directory after a successful backup.
    installed(target)
    retired = base / ('.pm-uninstalled-' + uuid.uuid4().hex)
    target.rename(retired)
    shutil.rmtree(retired)
    return {'action': 'uninstall', 'version': identity['version'], 'backup': saved,
            'other_skills_changed': False}


def restore(archive, skills_dir, backup_dir):
    compatible()
    _, target = target_path(skills_dir)
    if target.exists():
        installed(target)
    with tempfile.TemporaryDirectory(prefix='pm-restore-') as directory:
        root = Path(directory)
        with zipfile.ZipFile(archive) as z:
            names = set()
            if len(z.infolist()) > 2000:
                raise InstallError('archive-entry-limit')
            total = 0
            for item in z.infolist():
                if item.is_dir():
                    continue
                rel = relative(item.filename)
                if rel in names or (item.external_attr >> 16) & 0o170000 == 0o120000:
                    raise InstallError('duplicate-or-symlink-archive-entry')
                names.add(rel)
                total += item.file_size
                if total > 32 * 1024 * 1024:
                    raise InstallError('archive-size-limit')
                p = root / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(z.read(item))
        installed(root)  # rollback only accepts a verified installation backup
        return replace_package(root, skills_dir, backup_dir, update=target.exists())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['verify', 'install', 'update', 'uninstall', 'rollback'])
    parser.add_argument('--source', type=Path)
    parser.add_argument('--skills-dir', type=Path)
    parser.add_argument('--backup-dir', type=Path)
    parser.add_argument('--backup', type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'verify':
            result = verify(args.source or Path(__file__).resolve().parents[1])
        else:
            if not args.skills_dir:
                raise InstallError('explicit-skills-directory-required')
            if args.action in {'install', 'update'}:
                if not args.source:
                    raise InstallError('explicit-source-required')
                result = replace_package(args.source, args.skills_dir, args.backup_dir, args.action == 'update')
            elif args.action == 'uninstall':
                if not args.backup_dir:
                    raise InstallError('explicit-backup-directory-required')
                result = uninstall(args.skills_dir, args.backup_dir)
            else:
                if not args.backup or not args.backup_dir:
                    raise InstallError('explicit-backup-and-backup-directory-required')
                result = restore(args.backup, args.skills_dir, args.backup_dir)
        print(json.dumps({'result': 'passed', **result}, ensure_ascii=False))
    except (InstallError, OSError, ValueError, zipfile.BadZipFile) as error:
        print(json.dumps({'result': 'blocked', 'reason': str(error)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
