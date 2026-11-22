(function(){
  var hdr=document.getElementById('hdr'), sticky=document.getElementById('sticky'), entry=document.getElementById('entry');
  function onScroll(){var y=window.scrollY;hdr&&hdr.classList.toggle('sc',y>20);
    if(!sticky)return;
    var e=entry?entry.getBoundingClientRect().top:1e9;
    sticky.classList.toggle('on',y>500&&e>window.innerHeight);}
  window.addEventListener('scroll',onScroll,{passive:true});onScroll();

  // reveal (resting state stays visible if JS/IO unavailable)
  if('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches){
    var els=[].slice.call(document.querySelectorAll('.rv'));
    var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){en.target.classList.remove('pre');io.unobserve(en.target);}});},{rootMargin:'0px 0px -8% 0px'});
    els.forEach(function(el){if(el.getBoundingClientRect().top>window.innerHeight){el.classList.add('pre');io.observe(el);}});
  }

  // form → mailto
  var TO='info@ceokidsacademy.com';
  var f=document.getElementById('form'), msg=document.getElementById('form-msg');
  if(!f)return;
  // 職種ページからの「応募する」で希望職種を自動チェック（?job=classroom など）
  var JOBS={classroom:'教室運営・講師スタッフ',marketing:'生徒募集・イベント企画',partner:'加盟パートナー開校サポート',office:'事務局・オペレーション'};
  var m=/[?&]job=([a-z]+)/.exec(location.search);
  if(m&&JOBS[m[1]]){var cb=f.querySelector('input[name=job][value="'+JOBS[m[1]]+'"]');if(cb)cb.checked=true;}
  function v(id){return document.getElementById(id).value.trim();}
  function show(id,bad){document.getElementById(id).hidden=!bad;return bad;}
  f.addEventListener('submit',function(e){
    e.preventDefault();
    var jobs=[].slice.call(f.querySelectorAll('input[name=job]:checked')).map(function(i){return i.value;});
    var mail=document.getElementById('f-mail');
    var bad=[show('e-job',!jobs.length),show('e-name',!v('f-name')),show('e-kana',!v('f-kana')),
      show('e-mail',!v('f-mail')||!mail.checkValidity()),show('e-exp',!v('f-exp')),show('e-agree',!document.getElementById('f-agree').checked)];
    if(bad.indexOf(true)>-1){var first=f.querySelector('.err:not([hidden])');first&&first.parentNode.scrollIntoView({behavior:'smooth',block:'center'});return;}
    var kind=f.querySelector('input[name=kind]:checked').value;
    var body='【'+kind+'】\n希望職種：'+jobs.join('、')+'\nお名前：'+v('f-name')+'（'+v('f-kana')+'）\nメール：'+v('f-mail')+'\n電話：'+v('f-tel')+'\nお住まい：'+v('f-pref')+'\n希望の働き方：'+v('f-style')+'\n\n■これまでの経験\n'+v('f-exp')+'\n\n■志望動機・質問など\n'+v('f-msg');
    var subject='【運営社員 '+kind+'】'+jobs.join('・')+'（'+v('f-name')+'様）';
    msg.textContent='メールソフトが開き、'+TO+' 宛の文面が入力されます。そのまま送信してください。開かない場合は、このアドレスへ直接お送りください。';
    msg.hidden=false;
    location.href='mailto:'+TO+'?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(body);
  });
})();
