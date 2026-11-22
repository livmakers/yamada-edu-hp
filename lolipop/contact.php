<?php
/**
 * お問い合わせフォーム送信プログラム（ロリポップ！用）
 * 宛先: info@ceokidsacademy.com
 * ▼ 変更するのは下の「設定」部分だけです。
 */
declare(strict_types=1);

// ===== 設定（ここだけ書き換え） =====
const MAIL_TO     = 'info@ceokidsacademy.com';          // 届け先
const MAIL_FROM   = 'noreply@YOUR-DOMAIN';              // 送信元（独自ドメインのアドレス。ロリポップで作成推奨）
const FROM_NAME   = 'ヤマダ エデュケーション事業部 HP';
const SITE_ORIGIN = 'https://YOUR-DOMAIN';              // 本番URL（末尾スラッシュなし）
const SEND_AUTO_REPLY = true;                           // 相手への自動返信（true=送る / false=送らない）
const MIN_SECONDS = 4;      // 画面表示から送信までの最短秒数（機械の即送信を弾く）
const MAX_PER_HOUR = 5;     // 同じ接続元からの1時間あたり最大送信数
// =====================================

mb_language('Japanese');
mb_internal_encoding('UTF-8');
header('Content-Type: application/json; charset=UTF-8');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');

session_set_cookie_params(['lifetime' => 0, 'path' => '/', 'secure' => true, 'httponly' => true, 'samesite' => 'Strict']);
session_name('yef');
session_start();

function out(int $code, array $data): void { http_response_code($code); echo json_encode($data, JSON_UNESCAPED_UNICODE); exit; }
function clean(string $s, int $max): string {
  $s = str_replace(["\r\n", "\r"], "\n", $s);
  $s = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $s) ?? '';
  return mb_substr(trim($s), 0, $max);
}
function oneline(string $s, int $max): string { return clean(str_replace("\n", ' ', $s), $max); }

// --- 1) 合言葉（トークン）を配る ---
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
  $_SESSION['tok'] = bin2hex(random_bytes(32));
  $_SESSION['t0']  = time();
  out(200, ['token' => $_SESSION['tok']]);
}
if ($_SERVER['REQUEST_METHOD'] !== 'POST') out(405, ['ok' => false, 'error' => '不正なアクセスです。']);

// --- 2) よその画面からの送信を拒否 ---
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '' && strpos(SITE_ORIGIN, 'YOUR-DOMAIN') === false
    && $origin !== SITE_ORIGIN && $origin !== str_replace('://', '://www.', SITE_ORIGIN)) {
  out(403, ['ok' => false, 'error' => '不正な送信元です。']);
}

// --- 3) 合言葉チェック（なりすまし防止） ---
$tok = (string)($_POST['token'] ?? '');
if (empty($_SESSION['tok']) || !hash_equals($_SESSION['tok'], $tok)) {
  out(400, ['ok' => false, 'error' => '画面の有効期限が切れました。ページを再読み込みして、もう一度お試しください。']);
}
$elapsed = time() - (int)($_SESSION['t0'] ?? 0);
unset($_SESSION['tok']); // 使い捨て
if ($elapsed < MIN_SECONDS || $elapsed > 7200) out(400, ['ok' => false, 'error' => 'もう一度お試しください。']);

// --- 4) 罠の入力欄（人には見えない）に何か入っていたらロボット ---
if (($_POST['website'] ?? '') !== '') out(200, ['ok' => true]); // ロボットには成功したふり

// --- 5) 連続送信の制限 ---
$dir = __DIR__ . '/_data';
if (!is_dir($dir)) { @mkdir($dir, 0700); @file_put_contents($dir . '/.htaccess', "Require all denied\n"); }
$ipKey = $dir . '/rl_' . hash('sha256', ($_SERVER['REMOTE_ADDR'] ?? '') . 'yef') . '.json';
$hits = is_file($ipKey) ? (json_decode((string)file_get_contents($ipKey), true) ?: []) : [];
$hits = array_values(array_filter($hits, fn($t) => $t > time() - 3600));
if (count($hits) >= MAX_PER_HOUR) out(429, ['ok' => false, 'error' => '短時間に送信が続いたため受付を一時停止しています。時間をおいて、またはメールでご連絡ください。']);

// --- 6) 入力チェック ---
$kinds = ['加盟のお問い合わせ', '個別相談', 'その他'];
$types = ['個人・主婦（未経験）', '教室・塾を運営中', '教育事業者・法人', 'その他'];
$kind  = in_array($_POST['kind'] ?? '', $kinds, true) ? $_POST['kind'] : 'その他';
$type  = in_array($_POST['type'] ?? '', $types, true) ? $_POST['type'] : 'その他';
$name  = oneline((string)($_POST['name'] ?? ''), 60);
$org   = oneline((string)($_POST['org'] ?? ''), 100);
$email = oneline((string)($_POST['email'] ?? ''), 254);
$tel   = oneline((string)($_POST['tel'] ?? ''), 30);
$area  = oneline((string)($_POST['area'] ?? ''), 100);
$msg   = clean((string)($_POST['msg'] ?? ''), 3000);
$agree = ($_POST['agree'] ?? '') === 'on';

if (!$agree) out(422, ['ok' => false, 'error' => 'プライバシーポリシーへの同意にチェックを入れてください。']);
if ($name === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) out(422, ['ok' => false, 'error' => 'お名前と、正しい形式のメールアドレスを入力してください。']);
if ($tel !== '' && !preg_match('/^[0-9０-９+\-－ ()（）]{6,30}$/u', $tel)) out(422, ['ok' => false, 'error' => '電話番号の形式をご確認ください。']);
// 迷惑メールによくある「リンクだらけ」の本文を拒否
if (preg_match_all('#https?://#i', $msg) > 2) out(422, ['ok' => false, 'error' => '本文にURLが多すぎます。URLは2つまでにしてください。']);

// --- 7) メール送信（送信元とReturn-Pathを同じ独自ドメインのアドレスに揃える＝迷惑メール判定対策） ---
$now = date('Y-m-d H:i');
$body = "ホームページからお問い合わせがありました。\n\n"
  . "【ご希望】{$kind}\n【お名前】{$name}\n【会社名・教室名】{$org}\n【メール】{$email}\n【電話】{$tel}\n"
  . "【ご状況】{$type}\n【検討エリア】{$area}\n\n【ご質問など】\n{$msg}\n\n"
  . "----\n受信日時：{$now}\n※このメールに返信すると、お問い合わせ者に直接届きます。\n";
$subject = '【CEOキッズアカデミー加盟】' . $kind . '（' . $name . '様）';
$fromHdr = 'From: ' . mb_encode_mimeheader(FROM_NAME) . ' <' . MAIL_FROM . '>';
$headers = $fromHdr . "\r\nReply-To: " . $email . "\r\nX-Mailer: yef-form";
$ok = mb_send_mail(MAIL_TO, $subject, $body, $headers, '-f' . MAIL_FROM);
if (!$ok) out(500, ['ok' => false, 'error' => '送信に失敗しました。お手数ですが info@ceokidsacademy.com へ直接メールでご連絡ください。']);

$hits[] = time();
@file_put_contents($ipKey, json_encode($hits), LOCK_EX);

// 自動返信は本文を載せない（第三者への迷惑メール送信に悪用されないため）
if (SEND_AUTO_REPLY) {
  $reply = "{$name} 様\n\nこのたびはCEOキッズアカデミーの加盟についてお問い合わせいただき、ありがとうございます。\n"
    . "内容を確認のうえ、担当者より個別にご連絡いたします。\n\n"
    . "【ご希望】{$kind}\n\n"
    . "※本メールは送信専用です。ご連絡は " . MAIL_TO . " までお願いいたします。\n\n"
    . "株式会社ヤマダ エデュケーション事業部\n〒166-0004 東京都杉並区阿佐谷南3-1-27\n" . MAIL_TO . "\n";
  mb_send_mail($email, '【受付完了】お問い合わせありがとうございます', $reply,
    $fromHdr . "\r\nReply-To: " . MAIL_TO, '-f' . MAIL_FROM);
}
out(200, ['ok' => true]);
