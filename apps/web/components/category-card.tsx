export function CategoryCard({ kicker, title, description, href }: { kicker: string; title: string; description: string; href: string }) {
  return (
    <a className="category-card" href={href}>
      <div><span className="eyebrow">{kicker}</span><h3>{title}</h3><p>{description}</p></div>
      <span className="card-link">Explore rankings →</span>
    </a>
  );
}
