"""Cập nhật các trang web từ file Word mới mà vẫn giữ những chỗ đã sửa thẳng trên trang web.

GitHub chạy file này tự động (xem .github/workflows/build.yml) trước mỗi lần tạo trang.
Có thể chạy tay:  python3 tools/sync_from_word.py [--prefer-word]

Cách làm
  - Tag `word-base` giữ "bản gốc": các trang được tạo từ file Word lần trước, chưa có chỗ sửa trên web.
  - Nếu file Word không đổi so với bản gốc: không làm gì.
  - Nếu file Word đã đổi: tạo trang mới từ Word, rồi gộp từng trang theo 3 bản
        bản gốc (Word lần trước)  ->  trang hiện tại (có chỗ sửa trên web)
                                  ->  trang mới (từ Word mới)
    Đoạn chỉ sửa trên web: giữ. Đoạn chỉ đổi trong Word: cập nhật. Cả hai sửa giống nhau: giữ.
  - Cùng một đoạn bị sửa khác nhau ở cả hai nơi ("trùng"): không đổi trang nào, ghi báo cáo,
    trả mã 2. Chạy với --prefer-word thì ở những đoạn trùng lấy nội dung Word.

Tên file Word: source_GT32U2086_SDK_User_Guide.docx (ở thư mục gốc). File .docx tải lên thư mục gốc
với tên khác sẽ được coi là file Word mới: đổi về tên chuẩn, bản cũ bị thay thế.

Mã trả về: 0 = xong, 2 = có đoạn trùng (chưa cập nhật), khác = lỗi.
"""
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORD = 'source_GT32U2086_SDK_User_Guide.docx'
TAG = 'word-base'
PREFER_WORD = '--prefer-word' in sys.argv
SUMMARY = os.environ.get('GITHUB_STEP_SUMMARY')

LABEL_WEB, LABEL_BASE, LABEL_WORD = 'trang web', 'Word lần trước', 'file Word mới'


def git(*args, check=True, env=None, binary=False):
    r = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, env=env)
    if check and r.returncode != 0:
        raise SystemExit(f'git {" ".join(args)} lỗi:\n{r.stderr.decode(errors="replace")}')
    return r.stdout if binary else r.stdout.decode(errors='replace').strip()


def managed(path):
    """Files written by tools/docx_to_pages.py."""
    return (path == 'README.md' or path.startswith('pages/') or path == 'theme/gt32u2086_nav.js'
            or (path.startswith('images/') and os.path.basename(path).startswith('word_')))


def is_binary(path):
    return path.startswith('images/')


def say(text):
    print(text)
    if SUMMARY:
        with open(SUMMARY, 'a', encoding='utf-8') as f:
            f.write(text + '\n')


def read(path):
    p = os.path.join(ROOT, path)
    return open(p, 'rb').read() if os.path.isfile(p) else None


def base_file(path):
    r = subprocess.run(['git', 'show', f'{TAG}:{path}'], cwd=ROOT, capture_output=True)
    return r.stdout if r.returncode == 0 else None


# ------------------------------------------------------------------ 1. the Word file
def normalize_word():
    """A .docx uploaded to the root under another name becomes the new Word file."""
    others = [f for f in os.listdir(ROOT) if f.lower().endswith('.docx') and f != WORD and not f.startswith('~$')]
    if not others:
        return
    def when(f):
        t = git('log', '-1', '--format=%ct', '--', f, check=False)
        return int(t) if t.isdigit() else int(os.path.getmtime(os.path.join(ROOT, f)))
    newest = max(others, key=when)
    if os.path.exists(os.path.join(ROOT, WORD)) and when(WORD) > when(newest):
        say(f'- Bỏ qua `{newest}`: file Word chuẩn mới hơn.')
        return
    os.replace(os.path.join(ROOT, newest), os.path.join(ROOT, WORD))
    for f in others:
        if f != newest:
            os.remove(os.path.join(ROOT, f))
    say(f'- Dùng file Word mới tải lên `{newest}` (đổi tên thành `{WORD}`).')


# ------------------------------------------------------------------ 2. remember the generated pages
def save_base(src_dir):
    """Store the pages generated from Word (no web edits) as a commit outside the branch, tag it."""
    idx = os.path.join(tempfile.mkdtemp(), 'index')
    env = dict(os.environ, GIT_INDEX_FILE=idx)
    git('read-tree', '--empty', env=env)
    for dirpath, _, files in os.walk(src_dir):
        for name in files:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, src_dir).replace(os.sep, '/')
            if managed(rel) or rel == WORD:
                blob = git('hash-object', '-w', full)
                git('update-index', '--add', '--cacheinfo', f'100644,{blob},{rel}', env=env)
    tree = git('write-tree', env=env)
    commit = git('commit-tree', tree, '-m', 'Trang tạo từ file Word (bản gốc để gộp)')
    git('tag', '-f', TAG, commit)


def generate(tmp):
    """Run docx_to_pages.py on a copy of the project; return the copy's path."""
    out = os.path.join(tmp, 'gen')
    shutil.copytree(ROOT, out, ignore=shutil.ignore_patterns('.git', 'build', 'node_modules'))
    r = subprocess.run([sys.executable, 'tools/docx_to_pages.py', WORD], cwd=out, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        say('**Lỗi khi đọc file Word:**\n```\n' + r.stderr[-3000:] + '\n```')
        raise SystemExit(1)
    return out


def files_under(top):
    found = set()
    for dirpath, dirs, files in os.walk(top):
        dirs[:] = [d for d in dirs if d not in ('.git', 'build', 'node_modules')]
        for name in files:
            rel = os.path.relpath(os.path.join(dirpath, name), top).replace(os.sep, '/')
            if managed(rel):
                found.add(rel)
    return found


def merge3(path, cur, base, new, tmp):
    """3-way merge of one text file. Returns (text, number_of_conflicts)."""
    paths = []
    for tag, data in (('cur', cur), ('base', base), ('new', new)):
        p = os.path.join(tmp, tag + '_' + path.replace('/', '_'))
        open(p, 'wb').write(data)
        paths.append(p)
    args = ['git', 'merge-file', '-p', '-L', LABEL_WEB, '-L', LABEL_BASE, '-L', LABEL_WORD]
    if PREFER_WORD:
        args.append('--theirs')
    r = subprocess.run(args + paths, capture_output=True)
    if r.returncode < 0:
        raise SystemExit(f'Gộp {path} lỗi')
    return r.stdout, r.returncode


def conflict_blocks(text):
    """Pull 'web vs Word' pairs out of a merged text with conflict markers."""
    blocks, web, word, state = [], [], [], None
    for line in text.decode(errors='replace').split('\n'):
        if line.startswith('<<<<<<< '):
            state, web, word = 'web', [], []
        elif line.startswith('=======') and state == 'web':
            state = 'word'
        elif line.startswith('>>>>>>> ') and state == 'word':
            blocks.append(('\n'.join(web).strip(), '\n'.join(word).strip()))
            state = None
        elif state == 'web':
            web.append(line)
        elif state == 'word':
            word.append(line)
    return blocks


def short(s, n=600):
    s = s or '(trống)'
    return s if len(s) <= n else s[:n] + ' …'


# ------------------------------------------------------------------ main
def main():
    first_run = not git('rev-parse', '-q', '--verify', f'refs/tags/{TAG}', check=False)
    if first_run:
        git('tag', '-f', TAG, 'HEAD')
        say('- Lần chạy đầu: lấy các trang hiện có làm bản gốc từ file Word.')

    normalize_word()
    word_now = read(WORD)
    if word_now is None:
        say(f'- Không thấy file `{WORD}`: tạo trang từ các file trang hiện có.')
        return 0
    if base_file(WORD) == word_now:
        print('File Word không đổi: tạo trang từ các file trang hiện có.')
        return 0

    say('### Có file Word mới: cập nhật các trang')
    tmp = tempfile.mkdtemp()
    gen = generate(tmp)

    base_set = {p for p in git('ls-tree', '-r', '--name-only', TAG).split('\n') if p and managed(p)}
    new_set, cur_set = files_under(gen), files_under(ROOT)
    writes, deletes, conflicts, kept_web = {}, [], [], []

    for path in sorted(base_set | new_set | cur_set):
        b = base_file(path) if path in base_set else None
        c = read(path)
        n = open(os.path.join(gen, path), 'rb').read() if path in new_set else None
        if n is None and b is None:
            continue                                   # page added on the web only: leave it
        if is_binary(path):                            # pictures from Word: Word wins
            if n is None:
                deletes.append(path)
            elif c != n:
                writes[path] = n
            continue
        if n is None:                                  # chapter removed from Word
            if c is None:
                continue
            if c == b or PREFER_WORD:
                deletes.append(path)
            else:
                conflicts.append((path, [('(trang đã sửa trên web)', '(chương này không còn trong file Word mới)')]))
            continue
        if c is None or c == b or c == n:              # no web edit on this page (or same edit)
            if c != n:
                writes[path] = n
            continue
        if b is None:                                  # same new file name on both sides, different text
            if PREFER_WORD:
                writes[path] = n
            else:
                conflicts.append((path, [(short(c.decode(errors='replace')), short(n.decode(errors='replace')))]))
            continue
        if n == b:                                     # only the web changed this page
            kept_web.append(path)
            continue
        merged, nconf = merge3(path, c, b, n, tmp)
        if nconf and not PREFER_WORD:
            conflicts.append((path, conflict_blocks(merged)))
        else:
            writes[path] = merged
            kept_web.append(path)

    if conflicts:
        say('\n## File Word mới CHƯA được cập nhật vào trang web\n')
        say('Có đoạn bị sửa khác nhau ở cả file Word và trên trang web. Trang web vẫn giữ nội dung '
            'hiện tại, chưa có thay đổi nào từ file Word mới.\n')
        for path, blocks in conflicts:
            say(f'**{path}**\n')
            for web, word in blocks:
                say(f'- Trên trang web:\n\n```\n{short(web)}\n```\n- Trong file Word mới:\n\n```\n{short(word)}\n```\n')
        say('**Cách xử lý (chọn một):**\n\n'
            '1. Sửa file Word cho giống chỗ đã sửa trên trang web, rồi tải file Word lên lại.\n'
            '2. Lấy nội dung Word ở những đoạn trùng: tab **Actions** → **Tao trang tai lieu** → '
            '**Run workflow** → đánh dấu ô "Lấy nội dung file Word ở những đoạn bị sửa khác nhau" → '
            '**Run workflow**. Các chỗ sửa khác trên web vẫn được giữ.\n')
        return 2

    for path, data in writes.items():
        full = os.path.join(ROOT, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, 'wb').write(data)
    for path in deletes:
        if os.path.exists(os.path.join(ROOT, path)):
            os.remove(os.path.join(ROOT, path))
    save_base(gen)

    say(f'- Cập nhật {len(writes)} file, xoá {len(deletes)} file theo file Word mới.')
    if kept_web:
        say('- Giữ chỗ sửa trên trang web ở: ' + ', '.join(f'`{p}`' for p in sorted(set(kept_web))))
    if PREFER_WORD:
        say('- Đoạn bị sửa khác nhau: đã lấy nội dung file Word.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
