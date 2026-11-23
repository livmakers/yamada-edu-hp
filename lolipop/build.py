#!/usr/bin/env python3
"""ロリポップ用ファイル一式を作る。使い方: python3 lolipop/build.py 本番ドメイン（例 example.jp）"""
import sys, shutil, pathlib, re, zipfile
arg = (sys.argv[1] if len(sys.argv) > 1 else 'YOUR-DOMAIN').strip().replace('https://','').replace('http://','')
dom, _, sub = arg.partition('/')            # 例 web-yamada.co.jp/edu/ → dom=web-yamada.co.jp, sub=edu
sub = sub.strip('/')
prefix = '/' + (sub + '/' if sub else '')   # サイトの置き場所（/ または /edu/）
root = pathlib.Path(__file__).resolve().parent.parent
out = root / 'lolipop' / 'dist' / 'yamada-edu-hp'
if out.exists(): shutil.rmtree(out)
out.mkdir(parents=True)
for f in ['index.html','privacy.html','404.html','robots.txt','sitemap.xml','llms.txt','favicon.svg']:
    shutil.copy(root/f, out/f)
shutil.copytree(root/'img', out/'img')
shutil.copy(root/'lolipop'/'htaccess.txt', out/'htaccess.txt')  # SSL完了後にロリポップFTPで .htaccess に名前変更
base = f'https://{dom}{prefix}'
for f in ['index.html','privacy.html','robots.txt','sitemap.xml','llms.txt']:
    p = out/f; s = p.read_text(encoding='utf-8')
    s = s.replace('https://livmakers.github.io/yamada-edu-hp/', base)
    p.write_text(s, encoding='utf-8')
p = out/'404.html'; p.write_text(p.read_text(encoding='utf-8').replace('/yamada-edu-hp/', prefix), encoding='utf-8')
p = out/'htaccess.txt'; h = p.read_text(encoding='utf-8').replace('ErrorDocument 404 /404.html', f'ErrorDocument 404 {prefix}404.html')
if sub:  # 既存サイトの一部に置く場合、ドメイン全体に効くHSTSは既存サイトに影響するので外す
    h = '\n'.join(l for l in h.splitlines() if 'Strict-Transport-Security' not in l) + '\n'
p.write_text(h, encoding='utf-8')
# PHPフォーム
php = (root/'lolipop'/'contact.php').read_text(encoding='utf-8').replace('YOUR-DOMAIN', dom).replace("'path' => '/'", f"'path' => '{prefix}'")
(out/'contact.php').write_text(php, encoding='utf-8')
# index.html: CSP・罠欄・送信処理をPHP版に
p = out/'index.html'; s = p.read_text(encoding='utf-8')
s = s.replace("form-action 'self' mailto:", "form-action 'self'")
s = s.replace('<div class="full"><button class="btn btn-gold" type="submit">',
  '<div class="hp" aria-hidden="true"><label for="f-web">ウェブサイト（入力不要）</label><input id="f-web" name="website" tabindex="-1" autocomplete="off"></div>\n      <div class="full"><button class="btn btn-gold" type="submit" id="f-send">', 1)
s = s.replace('</style>', '.cform .hp{position:absolute!important;left:-9999px!important;width:1px;height:1px;overflow:hidden}\n</style>', 1)
a = s.index('  // form → mail to info@ceokidsacademy.com'); b = s.index('})();\n</script>', a)
js = r'''  // form → contact.php（サーバーから info@ceokidsacademy.com へ送信）
  var form=document.getElementById('cform'), tok='';
  function getTok(){ return fetch('contact.php',{credentials:'same-origin',cache:'no-store'}).then(function(r){return r.json();}).then(function(j){tok=j.token||'';}).catch(function(){}); }
  getTok();
  form.addEventListener('submit', function(e){
    e.preventDefault();
    var name=document.getElementById('f-name'), mail=document.getElementById('f-mail'), msg=document.getElementById('form-msg'), btn=document.getElementById('f-send');
    var show=function(t){msg.textContent=t;msg.hidden=false;};
    if(!document.getElementById('f-agree').checked){show('プライバシーポリシーへの同意にチェックを入れてください。');document.getElementById('f-agree').focus();return;}
    if(!name.value.trim()||!mail.value.trim()||!mail.checkValidity()){show('お名前と、正しい形式のメールアドレスを入力してください。');(name.value.trim()?mail:name).focus();return;}
    var fd=new FormData(form); fd.append('token',tok);
    btn.disabled=true; show('送信しています…');
    fetch('contact.php',{method:'POST',body:fd,credentials:'same-origin'}).then(function(r){return r.json();}).then(function(j){
      if(j.ok){ form.reset(); show('送信が完了しました。ご入力のメールアドレスに受付メールをお送りしました（届かない場合は迷惑メールフォルダもご確認ください）。担当者より個別にご連絡いたします。'); }
      else { show(j.error||'送信できませんでした。info@ceokidsacademy.com へ直接メールでご連絡ください。'); }
    }).catch(function(){ show('通信エラーで送信できませんでした。お手数ですが info@ceokidsacademy.com へ直接メールでご連絡ください。'); })
    .then(function(){ btn.disabled=false; getTok(); });
  });
'''
s = s[:a] + js + s[b:]
p.write_text(s, encoding='utf-8')
# privacy.html: 外部サービスの記述をロリポップ用に
p = out/'privacy.html'; s = p.read_text(encoding='utf-8')
s = s.replace('また、当ウェブサイトはGitHub Pages（GitHub, Inc.）で公開しており、同社のサーバーにアクセス記録が残ります。',
  'また、当ウェブサイトはロリポップ！レンタルサーバー（GMOペパボ株式会社）で公開しており、同社のサーバーにアクセス記録が残ります。お問い合わせフォームでは、なりすまし送信を防ぐためだけに一時的なCookie（ブラウザを閉じると消えるもの）を使用します。')
p.write_text(s, encoding='utf-8')
leftover = [f.name for f in out.rglob('*') if f.is_file() and f.suffix in ('.html','.txt','.xml','.php') and 'github.io' in f.read_text(encoding='utf-8')]
zp = root/'lolipop'/'dist'/(sys.argv[2] if len(sys.argv) > 2 else 'yamada-edu-hp-lolipop.zip')
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(out.rglob('*')):
        if f.is_file(): z.write(f, 'yamada-edu-hp/'+str(f.relative_to(out)))
print('url:', base, '| github.io残り:', leftover or 'なし', '| zip:', zp)
