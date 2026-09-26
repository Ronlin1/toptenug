import { CategoryCard } from "../components/category-card";
import { MetricCard } from "../components/metric-card";
import { safeApiGet, type DashboardData } from "../lib/api";

export default async function HomePage() {
  const dashboard = await safeApiGet<DashboardData>("/v1/dashboard", { current_quarter: null, indexed_entities: 0, active_rankings: 0, published_snapshots: 0 });
  return <main>
    <section className="hero"><div className="eyebrow">Uganda&apos;s quarterly digital intelligence index</div><h1>Uganda,<br/>ranked by data.</h1><p className="hero-copy">Discover the people, builders, products, communities and media shaping Uganda&apos;s digital ecosystem—with evidence you can inspect and algorithms you can understand.</p></section>
    <section className="grid metrics">
      <MetricCard value={dashboard.current_quarter ?? "Building"} label="Current official index" />
      <MetricCard value={dashboard.indexed_entities.toLocaleString()} label="Entities indexed" />
      <MetricCard value={dashboard.active_rankings} label="Active ranking families" />
      <MetricCard value={dashboard.published_snapshots} label="Quarterly snapshots" />
    </section>
    <div className="section-head"><div><span className="eyebrow">Explore Uganda</span><h2>Ranking universes</h2></div><p>Start with technology and open source. Media, startups, creators, research and more plug into the same evidence engine next.</p></div>
    <section className="grid cards">
      <CategoryCard kicker="Live first" title="Technology & Builders" description="Developers, AI/ML, data, cloud, cybersecurity, open source and emerging technology." href="/technology" />
      <CategoryCard kicker="Coming next" title="Media & Creators" description="TV, radio, YouTube, podcasts, creators and digital audience momentum." href="/" />
      <CategoryCard kicker="Coming next" title="Startups & Innovation" description="Ugandan startups, founders, products and sector-specific growth indexes." href="/" />
    </section>
  </main>;
}
