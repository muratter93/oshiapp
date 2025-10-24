(function() {
  const IS_AUTH = window.IS_AUTH === true;

  const fmt = n => Number(n).toLocaleString();

  // ------- 確認モーダル -------
  const confirmModal = document.getElementById('confirmModal');
  const okConfirmBtn = document.getElementById('okConfirmBtn');
  const cancelConfirmBtn = document.getElementById('cancelConfirmBtn');
  const confirmCoinsText = document.getElementById('confirmCoinsText');
  const confirmPriceText = document.getElementById('confirmPriceText');
  const hiddenForm = document.getElementById('hiddenBuyForm');
  let pendingUrl = null;

  function openConfirm(url, coins, price) {
    pendingUrl = url;
    confirmCoinsText.textContent = fmt(coins);
    confirmPriceText.textContent = fmt(price);
    confirmModal.style.display = 'block';
  }
  function closeConfirm() {
    pendingUrl = null;
    confirmModal.style.display = 'none';
  }
  okConfirmBtn?.addEventListener('click', () => {
    if (!pendingUrl) return;
    okConfirmBtn.disabled = true;
    hiddenForm.action = pendingUrl;
    hiddenForm.submit();
  });
  cancelConfirmBtn?.addEventListener('click', closeConfirm);
  confirmModal?.addEventListener('click', e => {
    if (e.target === confirmModal) closeConfirm();
  });

// ------- 完了モーダル -------
const doneModal     = document.getElementById('doneModal');
const doneOkBtn     = document.getElementById('doneOkBtn');
const doneCoinsText = document.getElementById('doneCoinsText');
const donePriceText = document.getElementById('donePriceText');
const donePointText = document.getElementById('donePointText');

const params = new URLSearchParams(window.location.search);
console.log("[money] done=", params.get('done'));
console.log("[money] donePointText exists?", !!donePointText);

if (params.get('done') === '1') {
  const coins  = Number(params.get('coins') || 0);
  const price  = Number(params.get('price') || 0);
  const points = Math.floor(coins / 100); // 100コイン→1pt

  if (doneCoinsText) doneCoinsText.textContent = coins.toLocaleString();
  if (donePriceText) donePriceText.textContent = price.toLocaleString();
  if (donePointText) donePointText.textContent = `${points} スタポ獲得しました！`;

  if (doneModal) doneModal.style.display = 'block';
  window.history.replaceState(null, '', window.location.pathname);
}

doneOkBtn?.addEventListener('click', () => { if (doneModal) doneModal.style.display = 'none'; });
doneModal?.addEventListener('click', e => { if (e.target === doneModal) doneModal.style.display = 'none'; });




  // ------- 認証誘導モーダル -------
  const authModal = document.getElementById('authModal');
  const authCancelBtn = document.getElementById('authCancelBtn');
  const authPriceText = document.getElementById('authPriceText');
  function openAuth(price) {
    if (authPriceText) authPriceText.textContent = fmt(price);
    authModal.style.display = 'block';
  }
  function closeAuth() { authModal.style.display = 'none'; }
  authCancelBtn?.addEventListener('click', closeAuth);
  authModal?.addEventListener('click', e => { if (e.target === authModal) closeAuth(); });

  // ------- 購入ボタン -------
  document.querySelectorAll('.purchase-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const url   = btn.dataset.url;
      const coins = btn.dataset.coins;
      const price = btn.dataset.price;
      if (IS_AUTH) {
        openConfirm(url, coins, price);
      } else {
        openAuth(price);
      }
    });
  });
})();
