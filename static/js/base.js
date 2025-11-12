function toggleMenu(element) {
    element.classList.toggle("active");
}


document.addEventListener('DOMContentLoaded', (event) => {
    const targetElement = document.getElementById('targetElement');
    const siteFooter = document.getElementById('siteFooter');

    // Intersection Observer のオプションを設定
    const options = {
        root: null, // ビューポートをルートとする
        rootMargin: '0px',
        threshold: 0.05 // フッターが10%表示されたらコールバックを実行
    };

    // Observerのコールバック関数
    const observerCallback = (entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // フッターと交差したら要素を非表示にする
                targetElement.classList.add('hidden');
            } else {
                // フッターと交差していなかったら要素を表示する
                targetElement.classList.remove('hidden');
            }
        });
    };

    // Intersection Observer のインスタンスを作成
    const observer = new IntersectionObserver(observerCallback, options);

    // フッターを監視対象として設定
    observer.observe(siteFooter);
});