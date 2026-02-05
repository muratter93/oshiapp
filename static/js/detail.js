

/* ❤️ ハートを飛ばす（.index 内に追加、position:fixed想定） */

function spawnHearts(button, count = 1) {
  const wrapper = button.closest('#detail_large_box') || document.body;
  const rect = button.getBoundingClientRect();

  for (let i = 0; i < count; i++) {
    const el = document.createElement('img');
    el.className = 'detail_heart'; // CSSは .detail_heart で定義
    el.src = 'static/img/heart-cl9.png';
    el.alt = 'heart';
    
    const x = rect.left + rect.width / 2 + (Math.random() - 0.5) * 40;
    const y = rect.top + rect.height / 2;
    el.style.left = `${x}px`;
    el.style.top = `${y}px`;

    // ここで飛ばす画像サイズ指定（例：幅30px）
    el.style.width = `50px`;
    el.style.position = 'fixed';
    el.style.pointerEvents = 'none'; // クリックを無視

    wrapper.appendChild(el);
    setTimeout(() => el.remove(), 4000);

  }

}