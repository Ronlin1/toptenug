import { CategoryCard } from "../../components/category-card";

export default function TechnologyPage() {
  return <main>
    <div className="breadcrumb"><a href="/">TopTenUG</a> / Technology</div>
    <section className="hero"><span className="eyebrow">Technology & Builders</span><h1 className="page-title">Uganda&apos;s builder pulse.</h1><p className="hero-copy">Open-source adoption, contribution activity, collaboration and verifiable public technology signals—without turning search popularity into rank.</p></section>
    <section className="grid cards">
      <CategoryCard kicker="DevRankUG 1.0" title="GitHub Developers" description="Our first evidence-driven builder index, based entirely on hard GitHub metrics." href="/technology/github-developers" />
      <CategoryCard kicker="Planned" title="AI & Data" description="AI engineers, researchers, data scientists and data engineers." href="/technology" />
      <CategoryCard kicker="Planned" title="Cloud & Infrastructure" description="Cloud, platform, DevOps, database and cybersecurity builders." href="/technology" />
    </section>
  </main>;
}
