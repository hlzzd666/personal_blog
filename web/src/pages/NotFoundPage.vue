<template>
  <main class="not-found-page">
    <div class="lost-coordinate" aria-hidden="true"><span>404</span><i></i></div>
    <p>ROUTE NOT FOUND</p>
    <h1>这条航线没有留下坐标</h1>
    <span>地址可能已经改变，也可能从未存在。</span>
    <nav>
      <RouterLink to="/">返回首页</RouterLink>
      <RouterLink to="/articles">浏览文章</RouterLink>
    </nav>
  </main>
</template>

<style scoped>
.not-found-page { display: grid; place-items: center; align-content: center; min-height: 100vh; padding: 8rem 1rem 4rem; overflow: hidden; color: #f4f0df; text-align: center; background: radial-gradient(circle at 50% 35%, rgba(117, 201, 189, 0.16), transparent 18rem), #051923; }
.lost-coordinate { position: relative; display: grid; place-items: center; width: min(22rem, 72vw); aspect-ratio: 1; margin-bottom: -3rem; border: 1px solid rgba(117, 201, 189, 0.16); border-radius: 50%; }
.lost-coordinate::before, .lost-coordinate::after { content: ""; position: absolute; inset: 17%; border: 1px dashed rgba(244, 202, 88, 0.23); border-radius: 50%; }
.lost-coordinate::after { inset: 39%; border-style: solid; }
.lost-coordinate span { color: rgba(244, 240, 223, 0.06); font: 900 clamp(7rem, 24vw, 13rem) var(--display-font); }
.lost-coordinate i { position: absolute; width: 44%; height: 1px; background: #f4ca58; transform: rotate(-28deg); transform-origin: left; animation: lost-scan 5s cubic-bezier(0.25, 1, 0.5, 1) infinite alternate; }
.not-found-page > p { margin: 0; color: #f4ca58; font: 700 0.68rem "IBM Plex Mono", monospace; }
.not-found-page h1 { margin: 0.8rem 0 0.5rem; font-family: var(--display-font); font-size: clamp(2rem, 7vw, 4rem); }
.not-found-page > span { color: rgba(244, 240, 223, 0.62); }
.not-found-page nav { display: flex; gap: 0.8rem; margin-top: 2rem; }
.not-found-page a { padding: 0.7rem 1rem; border: 1px solid rgba(117, 201, 189, 0.3); border-radius: 6px; color: #f4f0df; text-decoration: none; transition: transform 140ms cubic-bezier(0.22, 1, 0.36, 1), border-color 180ms ease; }
.not-found-page a:active { transform: scale(0.97); transition-duration: 0s; }
@keyframes lost-scan { from { transform: rotate(-45deg); } to { transform: rotate(20deg); } }
@media (prefers-reduced-motion: reduce) { .lost-coordinate i { animation: none; } .not-found-page a { transition: none; } }
</style>
