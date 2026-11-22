"""ロリポップ用のアップロード一式を作る。
使い方: python3 tools/build_lolipop.py example.jp  → dist/lolipop/ と dist/yamada-edu-lolipop.zip
GitHub Pages のURLを独自ドメインのURLに置き換え、.htaccess を同梱する。"""
import os, shutil, sys, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD = 'https://livmakers.github.io/yamada-edu-hp/'
INCLUDE = ['index.html', 'privacy.html', 'sitemap.xml', 'robots.txt', 'img', 'recruit']
HTACCESS = r'''# ===== 常時SSL（httpでアクセスされたらhttpsへ転送）=====
# ※ ロリポップの独自SSLが「SSL保護有効」になってからアップロードしてください
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteCond %{HTTP:X-Forwarded-Proto} !https
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
{WWW}
</IfModule>

# ===== セキュリティヘッダー =====
<IfModule mod_headers.c>
Header always set Strict-Transport-Security "max-age=31536000"
Header always set X-Content-Type-Options "nosniff"
Header always set X-Frame-Options "SAMEORIGIN"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()"
</IfModule>

# ===== 表示を速くする（画像・CSS・JSをブラウザに保存）=====
<IfModule mod_expires.c>
ExpiresActive On
ExpiresByType image/webp "access plus 30 days"
ExpiresByType image/jpeg "access plus 30 days"
ExpiresByType text/css "access plus 7 days"
ExpiresByType application/javascript "access plus 7 days"
</IfModule>
'''
def main(domain):
    domain = domain.strip().lower().removeprefix('https://').removeprefix('http://').strip('/')
    base = f'https://{domain}/'
    out = os.path.join(ROOT, 'dist', 'lolipop')
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    for name in INCLUDE:
        src = os.path.join(ROOT, name)
        (shutil.copytree if os.path.isdir(src) else shutil.copy2)(src, os.path.join(out, name))
    for d, _, fs in os.walk(out):
        for f in fs:
            if f.endswith(('.html', '.xml', '.txt')):
                p = os.path.join(d, f); s = open(p, encoding='utf-8').read()
                s = s.replace(OLD, base)
                s = s.replace('# 独自ドメイン運用時にドメイン直下で有効になります\n', '')
                open(p, 'w', encoding='utf-8').write(s)
    www = ('# www付きでアクセスされたら www なしへ統一\n'
           'RewriteCond %{HTTP_HOST} ^www\\.(.+)$ [NC]\n'
           'RewriteRule ^(.*)$ https://%1%{REQUEST_URI} [R=301,L]')
    hta = HTACCESS.replace('{WWW}', www)
    open(os.path.join(out, 'htaccess.txt'), 'w', encoding='utf-8').write(hta)
    z = os.path.join(ROOT, 'dist', 'yamada-edu-lolipop.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for d, _, fs in os.walk(out):
            for f in fs:
                p = os.path.join(d, f); zf.write(p, os.path.join('yamada-edu', os.path.relpath(p, out)))
    print(base, z)
if __name__ == '__main__':
    main(sys.argv[1])
