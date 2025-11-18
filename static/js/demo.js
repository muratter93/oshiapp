document.addEventListener('DOMContentLoaded', () => {
    const items = Array.from(document.querySelectorAll('.scroll-item'));

    let lastY = window.scrollY;

    function handleScroll() {
        const currentY = window.scrollY;
        const direction = currentY > lastY ? 'down' : 'up';
        lastY = currentY;

        const vh = window.innerHeight;

        items.forEach(item => {
            const rect = item.getBoundingClientRect();
            const mid = rect.top + rect.height / 2;

            if (direction === 'down') {
                // ▼ 下にスクロール中
                const isInViewDown = mid > vh * 0.1 && mid < vh * 0.9;
                if (isInViewDown) {
                    item.classList.add('show');
                }
            } else { // ▲ 上にスクロール中
                const isBelowEdge = rect.top > vh * 0.25;
                if (isBelowEdge) {
                    item.classList.remove('show');
                }
            }
        });
    }

    handleScroll();
    window.addEventListener('scroll', handleScroll);
});
