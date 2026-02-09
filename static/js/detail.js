/* ❤️ 主食とハートをランダムで飛ばす */

// 主食タイプ → 画像
const DIET_ICON_MAP = {
  A: '/static/img/food_meat.png',
  B: '/static/img/food_grass.png',
  C: '/static/img/food_fish.png',
  D: '/static/img/food_fruit.png',
  E: '/static/img/food_bug.png',
};

const DEFAULT_HEART = '/static/img/heart-cl9.png';

let lastType = null;
let streak = 0;

function spawnHearts(button, count = 1) {
  const wrapper = document.body;
  const rect = button.getBoundingClientRect();

  const diet = button.dataset.diet;  // ← HTMLから取得

  for (let i = 0; i < count; i++) {
    const el = document.createElement('img');
    el.className = 'detail_heart';
    el.alt = 'icon';

    let type;

    // ⭐ 3回続いたら次は逆にする
    if (streak >= 3) {
      type = lastType === 'food' ? 'heart' : 'food';
    } else {
      type = Math.random() < 0.5 ? 'food' : 'heart';
    }

    // 連続数を更新
    if (type === lastType) {
      streak++;
    } else {
      streak = 1;
      lastType = type;
    }

    const isFood = type === 'food';


    el.src = isFood
      ? (DIET_ICON_MAP[diet] || DEFAULT_HEART)
      : DEFAULT_HEART;

    const x = rect.left + rect.width / 2 + window.scrollX + (Math.random() - 0.5) * 40;
    const y = rect.top  + rect.height / 2 + window.scrollY;

    el.style.left = `${x}px`;
    el.style.top  = `${y}px`;
    el.style.width = '50px';
    el.style.pointerEvents = 'none';
    el.style.zIndex = 9999;

    wrapper.appendChild(el);
    setTimeout(() => el.remove(), 4000);
  }
}
