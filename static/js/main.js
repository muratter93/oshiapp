
document.querySelectorAll('.push-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const id = btn.dataset.id;

    try {
      const res = await fetch(`/like/${id}/`, {
        method: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken')},
      });
      const data = await res.json();

      if (data.total_point !== undefined) {
        // ① 推しポイント更新
        const card = btn.closest('.animal-card');
        card.querySelector('.point').textContent = data.total_point;

        // 💡 推しポイント数値を一瞬ピンクに
const pointElem = card.querySelector('.point');
if (pointElem) {
  pointElem.classList.add('flash');
  setTimeout(() => {
    pointElem.classList.remove('flash');
  }, 350); // 0.3秒後に戻す
}

        // ✅ 推しポイントのバッジをポンっと拡大
      const badge = card.querySelector('.oshii-badge');
      if (badge) {
        badge.classList.remove('pop');  // 連打時にリセット
        void badge.offsetWidth;         // reflow（再描画強制）
        badge.classList.add('pop');     // アニメ再生
      }


        // ② ウォレット残高・スタポ更新
        const walletElem = document.querySelector('#wallet-balance');
        const stapoElem = document.querySelector('#wallet-stapo');
        if (walletElem && data.cheer_coin_balance !== undefined) {
          walletElem.textContent = Number(data.cheer_coin_balance).toLocaleString();
        }
        if (stapoElem && data.stanning_point_balance !== undefined) {
          stapoElem.textContent = Number(data.stanning_point_balance).toLocaleString();
        }

        // ③ ハート演出
        spawnHearts(btn, 3);
// ④ 画像ズーム揺れ＋ホバー維持
const media = card.querySelector('.animal-media');
const img = media?.querySelector('img');
if (img && media) {
  // 押した瞬間から1.05維持
  img.classList.add('is-hoverlock');

  // 親に“揺れ”を付与（rotateのみなのでscaleと干渉しない）
  media.classList.remove('shake');
  void media.offsetWidth;
  media.classList.add('shake');

  // 揺れ終了後もロックは維持（hoverじゃなくても1.05のまま）
  media.addEventListener('animationend', () => {
    media.classList.remove('shake');
  }, { once: true });

  // マウスが外れたらロック解除（1.0へ自然に戻る）
  media.addEventListener('mouseleave', () => {
    img.classList.remove('is-hoverlock');
  }, { once: true });
}



      } else if (data.error) {
        alert(data.error);
      } else {
        alert('エラーが発生しました。');
      }

    } catch (err) {
      console.error(err);
      alert('通信に失敗しました。');
    }
  });
});

// ✅ CSRFトークン取得
function getCookie(name){
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/* ❤️ ハートを飛ばす */
function spawnHearts(button, count = 3) {
  const rect = button.getBoundingClientRect();
  for (let i = 0; i < count; i++) {
    const el = document.createElement('span');
    el.className = 'heart';
    el.textContent = '❤️';
    const startX = rect.left + rect.width / 2;
    const startY = rect.top + window.scrollY + 4;
    const offsetX = (Math.random() - 0.5) * 60;
    el.style.left = `${startX + offsetX}px`;
    el.style.top  = `${startY}px`;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 1000);
  }
}

// カードを順番に出す
function revealCards(stagger = 90, initialDelay = 120) {
  const cards = document.querySelectorAll('.animal-card');
  cards.forEach((card, i) => {
    card.classList.remove('is-revealed');           // まず隠す（リプレイ用）
    const delay = initialDelay + i * stagger;       // 90ms刻みでずらす
    setTimeout(() => card.classList.add('is-revealed'), delay);
  });
}

// 初回（ページ読み込み時）
window.addEventListener('DOMContentLoaded', () => {
  // ユーザーの簡略設定を尊重
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReduced) return;
  revealCards();
});

// もし「更新」ボタンがあるなら、それを押した時にも再生できる
// 例: <button id="refresh-btn">更新</button>
const refreshBtn = document.getElementById('refresh-btn');
if (refreshBtn) {
  refreshBtn.addEventListener('click', (e) => {
    e.preventDefault();
    // ここでリロードするなら location.reload();
    // もしくはAjaxで並び替え後にアニメだけ再生:
    revealCards();
  });
}
