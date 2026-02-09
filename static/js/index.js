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

const DIET_ICON_MAP = {
  A: '/static/img/food_meat1.png',
  B: '/static/img/food_grass2.png',
  C: '/static/img/food_fish3.png',
  D: '/static/img/food_fruit4.png',
  E: '/static/img/food_bug5.png',
};

const DEFAULT_HEART = '/static/img/heart-cl9.png';


// ⭐ ここに置く
function spawnHearts(button, count = 1) {
  const wrapper = document.body;
  const rect = button.getBoundingClientRect();
  const diet = button.dataset.diet;

  for (let i = 0; i < count; i++) {
    const el = document.createElement('img');
    el.className = 'index_heart';
    el.alt = 'icon';

    const isFood = Math.random() < 0.5;

    el.src = isFood
      ? (DIET_ICON_MAP[diet] || DEFAULT_HEART)
      : DEFAULT_HEART;

  const x = rect.left + rect.width / 2 + (Math.random() - 0.5) * 40;
  const y = rect.top  + rect.height / 2;

    el.style.left = `${x + window.scrollX}px`;
    el.style.top  = `${y + window.scrollY}px`;
    el.style.width = '50px';
    el.style.position = 'absolute';
    el.style.pointerEvents = 'none';
    el.style.zIndex = 9999;

    wrapper.appendChild(el);
    setTimeout(() => el.remove(), 4000);
  }

  // キラッ✨
  // button.classList.add('shine');
  // setTimeout(() => button.classList.remove('shine'), 700);
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

/* ========= 初期化（#index_mainbox_large コンテナごとに実行） ========= */
window.addEventListener('DOMContentLoaded', () => {
  const containers = document.querySelectorAll('#index_mainbox_large');
  if (!containers.length) return;

  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  containers.forEach(container => {
    // 1) ボタン：push（いいね）
    container.querySelectorAll('#index_push-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (btn.disabled) return;                // 連打防止
        btn.disabled = true;

        const id = btn.dataset.id;
        try {
            const res = await fetch(`/like/${id}/`, {
              method: 'POST',
              headers: { 'X-CSRFToken': getCookie('csrftoken') },
            });

            // まず JSON を読む（エラーでも読む）
            const data = await res.json().catch(() => ({}));

            // ★ HTTP 400系（コイン不足など）の場合
            if (!res.ok) {
              alert(data.error || 'エラーが発生しました。');
              return;
            }

            // ★ 成功（total_point が返ってくる）
            if (data.total_point !== undefined) {

            // ① 推しポイント更新
            const card = btn.closest('#index_animal_box');
            const pointElem = card?.querySelector('#index_point');
            const heartElem = card?.querySelector('#index_oshii-badge_lang');

            if (pointElem) {
              pointElem.textContent = data.total_point;

              // 数字
              pointElem.classList.add('flash');
              setTimeout(() => pointElem.classList.remove('flash'), 350);

              // ハート
              heartElem?.classList.add('flash-heart');
              setTimeout(() => heartElem?.classList.remove('flash-heart'), 350);
            }
            
              // バッジ演出
              const badge = card?.querySelector('#index_oshii-badge');
              if (badge) {
                badge.classList.remove('pop');
                void badge.offsetWidth;
                badge.classList.add('pop');
              }

              // 💫 現在のランキング順を取得（あなたの元コードのまま）
              function getCurrentRankingOrder() {
                const current = [];
                document.querySelectorAll('#index_animal_ranking_sidebar #index_animal_ranking_list li').forEach(li => {
                  const nameEl = li.querySelector('.index_rank_japanese');
                  if (nameEl) current.push(nameEl.textContent.trim());
                });
                return current;
              }

              // 💫 UP↑エフェクト（最前面に出す版）
              function showUpEffect(targetEl) {
                const rect = targetEl.getBoundingClientRect();

                const up = document.createElement('span');
                up.textContent = 'UP↑';
                up.className = 'rank-up';

                up.style.position = 'absolute';
                up.style.left = rect.right + window.scrollX + 'px';
                up.style.top  = rect.top + window.scrollY + 'px';
                up.style.zIndex = '999999';
                up.style.pointerEvents = 'none';

                document.body.appendChild(up);

                setTimeout(() => up.remove(), 1200);
              }

              // 💫 CSSアニメーション追加（あなたのまま）
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

              // 💖 ランキング更新（あなたの元コードを維持）
              if (data.ranking_html) {
                const sidebar = document.querySelector('#index_animal_ranking_sidebar');
                if (sidebar) {
                  const oldRanking = getCurrentRankingOrder();
                  sidebar.outerHTML = data.ranking_html;
                  const newRanking = getCurrentRankingOrder();

                  newRanking.forEach((name, idx) => {
                    const oldIndex = oldRanking.indexOf(name);
                    if (oldIndex !== -1 && oldIndex > idx) {
                      const newLi = document.querySelectorAll('#index_animal_ranking_list li')[idx];
                      if (newLi) {
                        const nameEl = newLi.querySelector('.index_rank_japanese');
                        if (nameEl) showUpEffect(nameEl);
                      }
                    }
                  });
                }
              }

              // ② ウォレット更新
              const walletElem = document.querySelector('#wallet-balance');
              const stapoElem  = document.querySelector('#wallet-stapo');
              if (walletElem && data.cheer_coin_balance !== undefined) {
                walletElem.textContent = Number(data.cheer_coin_balance).toLocaleString();
              }
              if (stapoElem && data.stanning_point_balance !== undefined) {
                stapoElem.textContent = Number(data.stanning_point_balance).toLocaleString();
              }

              // ③ ハート演出
              spawnHearts(btn, 1);

              // ④ 画像の揺れ演出
              const media = card?.querySelector('#index_animal_box');
              const img = media?.querySelector('img');
              if (img && media) {
                img.classList.add('is-hoverlock');
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

            // ★ 成功ではないが error が返ってきた場合（保険）
            } else if (data.error) {
              alert(data.error);

            // ★ 何も情報がない場合
            } else {
              alert('エラーが発生しました。');
            }

          } catch (err) {
            console.error(err);
            // ★ 本当の通信エラーの場合のみ
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
    container.querySelectorAll('#index_mainbox').forEach(grid => shuffleChildren(grid));

    // 5) カルーセル初期化（コンテナ内）
    container.querySelectorAll('.carousel').forEach(setupCarousel);
  });
});

