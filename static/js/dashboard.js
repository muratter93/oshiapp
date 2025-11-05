document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".menu-section").forEach((section) => {
    const icon = section.querySelector(".menu-icon");
    const next = section.nextElementSibling;

    // 初期状態：オープン
    let isOpen = true;
    if (next && next.classList.contains("menu-items")) {
      next.style.display = "block"; // ← 最初から開く
    }
    if (icon) icon.textContent = "▼"; // ← アイコンも▼にしておく

    // クリックで開閉切り替え
    section.addEventListener("click", () => {
      if (!next || !next.classList.contains("menu-items")) return;

      isOpen = !isOpen;
      next.style.display = isOpen ? "block" : "none";
      if (icon) icon.textContent = isOpen ? "▼" : "▶";
    });
  });
});
