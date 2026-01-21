(function () {
  const IS_AUTH = window.IS_AUTH === true;
  const fmt = n => Number(n).toLocaleString();

  /* ========= 確認モーダル ========= */
  const confirmModal = document.getElementById('confirmModal');
  const okConfirmBtn = document.getElementById('okConfirmBtn');
  const cancelConfirmBtn = document.getElementById('cancelConfirmBtn');
  const confirmCoinsText = document.getElementById('confirmCoinsText');
  const confirmPriceText = document.getElementById('confirmPriceText');
  const payBackBtn = document.getElementById("payBackBtn");

  let selectedCoins = null;
  let selectedPrice = null;

  document.querySelectorAll(".purchase-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      if (!IS_AUTH) {
        document.getElementById("authModal").style.display = "block";
        return;
      }

      selectedCoins = btn.dataset.coins;
      selectedPrice = btn.dataset.price;

      confirmCoinsText.textContent = fmt(selectedCoins);
      confirmPriceText.textContent = fmt(selectedPrice);

      confirmModal.style.display = "block";
    });
  });

  okConfirmBtn.addEventListener("click", () => {
    confirmModal.style.display = "none";
    document.getElementById("payCoins").value = selectedCoins;
    document.getElementById("payModal").style.display = "block";

    initPayjp(); // ★ ここで初期化
  });

  cancelConfirmBtn?.addEventListener("click", () => {
    confirmModal.style.display = "none";
  });

  document.getElementById("authCancelBtn")?.addEventListener("click", () => {
  document.getElementById("authModal").style.display = "none";
});


  /* ========= 完了モーダル ========= */
const params = new URLSearchParams(window.location.search);
if (params.get('done') === '1') {
  document.getElementById('doneCoinsText').textContent =
    fmt(params.get('coins'));
  document.getElementById('donePriceText').textContent =
    fmt(params.get('price'));

  const doneModal = document.getElementById('doneModal');
  doneModal.style.display = 'block';

  // 👇 ここを追加
  const doneOkBtn = document.getElementById('doneOkBtn');
  if (doneOkBtn) {
    doneOkBtn.onclick = () => {
      doneModal.style.display = 'none';
      window.location.href = "/money/charge/";
    };
  }

  history.replaceState(null, '', location.pathname);
}


  /* ========= Pay.jp ========= */
  let payjp = null;
  let card = null;
  let initialized = false;

  function initPayjp() {
    if (initialized) return;

    payjp = Payjp(PAYJP_PUBLIC_KEY);
    const elements = payjp.elements();
    card = elements.create("card");

    card.mount("#card-number");

    const paySubmitBtn = document.getElementById("paySubmitBtn");
    paySubmitBtn.addEventListener("click", () => {
      paySubmitBtn.disabled = true;

      payjp.createToken(card).then(result => {
        if (result.error) {
          alert(result.error.message);
          paySubmitBtn.disabled = false;
          return;
        }

        document.getElementById("payjpToken").value = result.id;
        document.getElementById("payForm").submit();
      });
    });

    initialized = true;
  }

  payBackBtn?.addEventListener("click", () => {
  // カード入力モーダルを閉じる
  document.getElementById("payModal").style.display = "none";

  // 購入確認モーダルに戻す（不要ならこの行は消してOK）
  document.getElementById("confirmModal").style.display = "block";
  });

})();
