// ========= 共通ユーティリティ =========
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

/* ❤️ ハートを飛ばす（.index 内に追加、position:fixed想定） */
function spawnHearts(button, count = 3) {
  const wrapper = button.closest('.index') || document.body;
  const rect = button.getBoundingClientRect();
  for (let i = 0; i < count; i++) {
    const el = document.createElement('span');
    el.className = 'heart';               // CSSは .index .heart を定義しておく
    el.textContent = '❤️';
    const x = rect.left + rect.width / 2 + (Math.random() - 0.5) * 40;
    const y = rect.top  + rect.height / 2;
    el.style.left = `${x}px`;
    el.style.top  = `${y}px`;
    wrapper.appendChild(el);
    setTimeout(() => el.remove(), 1000);
  }
  // キラッ
  button.classList.add('shine');
  setTimeout(() => button.classList.remove('shine'), 700);
}

/* カードを順番に出す（コンテナ単位） */
function revealCards(container, stagger = 90, initialDelay = 120) {
  const cards = container.querySelectorAll('.animal-card');
  cards.forEach((card, i) => {
    card.classList.remove('is-revealed');  // リプレイ対応
    const delay = initialDelay + i * stagger;
    setTimeout(() => card.classList.add('is-revealed'), delay);
  });
}

/* シャッフル（Fisher–Yates） */
function shuffleChildren(parent) {
  const nodes = Array.from(parent.children);
  for (let i = nodes.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [nodes[i], nodes[j]] = [nodes[j], nodes[i]];
  }
  parent.innerHTML = '';
  nodes.forEach(n => parent.appendChild(n));
}

/* カルーセル（ホバーでだけオート、離すとその場で停止） */
function setupCarousel(carousel) {
  const slides = Array.from(carousel.querySelectorAll('.slide'));
  const dotsContainer = carousel.querySelector('.dots');
  if (!slides.length) return;

  const INTERVAL = Number(carousel.dataset.interval) || 1500;
  let current = 0, timer = null, isHovering = false;

  const goTo = (idx) => {
    current = (idx + slides.length) % slides.length;
    slides.forEach(s => s.classList.remove('active'));
    slides[current].classList.add('active');
    dotsContainer?.querySelectorAll('button').forEach((b, i) => {
      b.classList.toggle('active', i === current);
    });
  };
  const next = () => goTo(current + 1);
  const startAuto = () => { if (!timer && slides.length > 1) timer = setInterval(next, INTERVAL); };
  const stopAuto  = () => { if (timer) { clearInterval(timer); timer = null; } };

  if (dotsContainer) {
    dotsContainer.innerHTML = '';
    slides.forEach((_, i) => {
      const dot = document.createElement('button');
      dot.type = 'button';
      if (i === 0) dot.classList.add('active');
      dot.addEventListener('click', () => {
        goTo(i);
        if (isHovering) { stopAuto(); startAuto(); }
      });
      dotsContainer.appendChild(dot);
    });
  }

  goTo(0);
  carousel.addEventListener('mouseenter', () => { isHovering = true;  startAuto(); });
  carousel.addEventListener('mouseleave', () => { isHovering = false; stopAuto(); });
}

/* ========= 初期化（.index コンテナごとに実行） ========= */
window.addEventListener('DOMContentLoaded', () => {
  const containers = document.querySelectorAll('.index');
  if (!containers.length) return;

  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  containers.forEach(container => {
    // 1) ボタン：push（いいね）
    container.querySelectorAll('.push-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (btn.disabled) return;                // 連打防止
        btn.disabled = true;

        const id = btn.dataset.id;
        try {
          const res = await fetch(`/like/${id}/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
          });

          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const data = await res.json();

          if (data.total_point !== undefined) {
            // ① 推しポイント更新
            const card = btn.closest('.animal-card');
            const pointElem = card?.querySelector('.point');
            if (pointElem) {
              pointElem.textContent = data.total_point;
              // ピンク点滅（CSSは .index .point.flash 推奨）
              pointElem.classList.add('flash');
              setTimeout(() => pointElem.classList.remove('flash'), 350);
            }

            // バッジをポン
            const badge = card?.querySelector('.oshii-badge');
            if (badge) {
              badge.classList.remove('pop');
              void badge.offsetWidth;
              badge.classList.add('pop');
            }

            // 💫 現在のランキングを取得（HTML置換前に呼ぶ）
            function getCurrentRankingOrder() {
            const current = [];
            document.querySelectorAll('.animal-ranking-sidebar .animal-ranking-list li').forEach(li => {
                const nameEl = li.querySelector('.rank-japanese');
                if (nameEl) current.push(nameEl.textContent.trim());
            });
            return current;
            }

            // 💫 "UP"エフェクトを飛ばす
            function showUpEffect(targetEl) {
            const up = document.createElement('span');
            up.textContent = 'UP↑';
            up.className = 'rank-up';
            targetEl.style.position = 'relative';
            up.style.position = 'absolute';
            up.style.right = '-40px';
            up.style.top = '0';
            up.style.color = '#ff4081';
            up.style.fontWeight = 'bold';
            up.style.fontSize = '1.1rem';
            up.style.animation = 'flyUp 1.2s ease-out forwards';
            targetEl.appendChild(up);
            setTimeout(() => up.remove(), 1200);
            }

            // 💫 CSSアニメーションも追加
            const style = document.createElement('style');
            style.textContent = `
            @keyframes flyUp {
            0%   { transform: translateY(0); opacity: 1; }
            60%  { transform: translateY(-15px); opacity: 1; }
            100% { transform: translateY(-35px); opacity: 0; }
            }
            .rank-up {
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
            `;
            document.head.appendChild(style);


            // 💖ランキング更新（UPエフェクト付き）
            if (data.ranking_html) {
            const sidebar = document.querySelector('.animal-ranking-sidebar');
            if (sidebar) {
                // 1️⃣ 現在のランキングを記録
                const oldRanking = getCurrentRankingOrder();

                // 2️⃣ 一旦差し替え
                sidebar.outerHTML = data.ranking_html;

                // 3️⃣ 新しいランキングを取得
                const newRanking = getCurrentRankingOrder();

                // 4️⃣ 順位が上がった動物にUP↑演出
                newRanking.forEach((name, idx) => {
                const oldIndex = oldRanking.indexOf(name);
                if (oldIndex !== -1 && oldIndex > idx) {
                    // ランクが上がった
                    const newLi = document.querySelectorAll('.animal-ranking-list li')[idx];
                    if (newLi) {
                    const nameEl = newLi.querySelector('.rank-japanese');
                    if (nameEl) showUpEffect(nameEl);
                    }
                }
                });
            }
            }


            // ② ウォレット更新（グローバルID想定）
            const walletElem = document.querySelector('#wallet-balance');
            const stapoElem  = document.querySelector('#wallet-stapo');
            if (walletElem && data.cheer_coin_balance !== undefined) {
              walletElem.textContent = Number(data.cheer_coin_balance).toLocaleString();
            }
            if (stapoElem && data.stanning_point_balance !== undefined) {
              stapoElem.textContent = Number(data.stanning_point_balance).toLocaleString();
            }

            // ③ ハート演出
            spawnHearts(btn, 3);

            // ④ 画像ズーム揺れ＋ホバー維持
            const media = card?.querySelector('.animal-media');
            const img = media?.querySelector('img');
            if (img && media) {
              img.classList.add('is-hoverlock');     // 1.06維持（CSSで調整可）
              media.classList.remove('shake');
              void media.offsetWidth;
              media.classList.add('shake');
              media.addEventListener('animationend', () => {
                media.classList.remove('shake');
              }, { once: true });
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
        } finally {
          btn.disabled = false;
        }
      });
    });

    // 2) カード登場アニメ
    if (!prefersReduced) revealCards(container);

    // 3) 任意の「更新」ボタン（コンテナ内）
    const refreshBtn = container.querySelector('#refresh-btn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', (e) => {
        e.preventDefault();
        revealCards(container);
      });
    }

    // 4) 初期シャッフル（コンテナ内の全グリッド）
    container.querySelectorAll('.animal-grid').forEach(grid => shuffleChildren(grid));

    // 5) カルーセル初期化（コンテナ内）
    container.querySelectorAll('.carousel').forEach(setupCarousel);
  });
});