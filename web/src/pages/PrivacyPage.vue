<script setup lang="ts">
import { onMounted } from "vue";
import { useSeo } from "../composables/useSeo";

const { applySeo } = useSeo();
onMounted(() => applySeo({ title: "隐私说明", description: "了解本站如何使用访客位置、必要 Cookie 和文章统计信息。", canonicalPath: "/privacy" }));
</script>

<template>
  <main class="privacy-page">
    <header>
      <RouterLink to="/">← 返回首页</RouterLink>
      <p>PRIVACY / VISITOR NOTICE</p>
      <h1>隐私说明</h1>
      <span>这里说明本站会使用哪些信息，以及这些信息为什么会被使用。</span>
    </header>
    <article>
      <section>
        <h2>访客位置</h2>
        <p>当你打开首页时，本站会读取本次访问的 IP 地址，用于显示大致的国家、地区和城市，并在站长坐标已配置时计算大致距离。位置只用于这次页面展示，本站业务数据库不会保存原始 IP、定位结果或你的精确坐标。对于公网 IP，本站会将 IP 发送给定位服务商进行查询；本地网络地址不会进行公网定位。定位结果可能因网络、代理或服务商数据而不准确。</p>
      </section>
      <section>
        <h2>文章浏览与点赞</h2>
        <p>打开一篇文章会为该文章增加一次浏览统计；点赞数也会记录在文章统计中。为了避免同一浏览器重复点赞，本站会设置一个名为 article_visitor_id 的随机 Cookie，并将它转换为不可逆的匿名标识后保存，用于判断这台浏览器是否已经给某篇文章点过赞。这个标识不包含姓名、邮箱或原始 IP，也不会用于识别你的真实身份或建立兴趣画像。</p>
      </section>
      <section>
        <h2>Cookie 与本地数据</h2>
        <p>本站没有普通访客账号系统、评论系统或邮件订阅。除用于文章点赞去重的随机 Cookie 外，前台不会要求你提交姓名、邮箱、密码或其他个人资料。你可以在浏览器设置中删除或阻止 Cookie；这样可能会影响点赞去重功能，但不影响文章阅读。删除 Cookie 后，本站无法把新的匿名标识与之前的标识关联。</p>
      </section>
      <section>
        <h2>第三方服务</h2>
        <p>首页位置查询可能使用 IP 地理定位服务；“关于我”页面的城市地图可能使用高德地图服务。访问这些功能时，浏览器或服务器会按照对应服务商的隐私政策发送必要的网络请求。文章中的外部链接、转载来源和 RSS 阅读器也属于你主动访问的第三方服务，其数据处理不由本站控制。</p>
      </section>
      <section>
        <h2>服务器记录</h2>
        <p>为保证网站安全、排查故障和提供页面服务，网站运行环境或反向代理可能产生常规技术访问日志，例如请求时间、访问地址和网络地址。这些日志由部署环境按照其保留策略管理，不作为本站文章、点赞或访客位置业务数据使用。</p>
      </section>
      <section>
        <h2>管理后台</h2>
        <p>管理后台仅供站点管理员使用。管理员登录后会使用会话 Cookie 和安全校验 Cookie 维持登录状态；这些 Cookie 不用于普通访客，也不会向前台公开。</p>
      </section>
      <section>
        <h2>联系我们</h2>
        <p>如果你对本站的信息使用方式有疑问，可以通过“关于我”页面公开的联系方式联系站长。本站功能发生变化时，会同步更新这份说明。</p>
      </section>
    </article>
  </main>
</template>

<style scoped>
.privacy-page { min-height: 100vh; padding: 8.5rem clamp(1rem, 7vw, 7rem) 5rem; color: #173541; background: #edf2f5; font-family: "Noto Sans SC", sans-serif; }
.privacy-page header, .privacy-page article { width: min(800px, 100%); margin: 0 auto; }
.privacy-page header { padding-bottom: 2.5rem; border-bottom: 1px solid rgba(23, 53, 65, 0.16); }
.privacy-page header a { color: #c64f3a; text-decoration: none; }
.privacy-page header p { margin: 3rem 0 0.8rem; color: #c64f3a; font: 700 0.68rem "IBM Plex Mono", monospace; }
.privacy-page h1 { margin: 0; font-family: var(--display-font); font-size: clamp(3rem, 8vw, 6rem); }
.privacy-page header span { color: rgba(23, 53, 65, 0.68); }
.privacy-page article { display: grid; gap: 0; margin-top: 2.5rem; }
.privacy-page section { display: grid; grid-template-columns: 10rem minmax(0, 1fr); gap: 2rem; padding: 2rem 0; border-bottom: 1px solid rgba(23, 53, 65, 0.12); }
.privacy-page h2, .privacy-page p { margin: 0; }
.privacy-page h2 { font-family: var(--display-font); font-size: 1.35rem; }
.privacy-page p { color: rgba(23, 53, 65, 0.72); line-height: 1.9; }
@media (max-width: 620px) { .privacy-page section { grid-template-columns: 1fr; gap: 0.7rem; } }
</style>
