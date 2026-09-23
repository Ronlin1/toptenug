type Factor = { normalized?: number | null; weight?: number };

export function ScoreBreakdown({ factors }: { factors: Record<string, Factor> }) {
  return <section className="breakdown"><h2 className="chart-title">Score breakdown</h2>{Object.entries(factors).length ? Object.entries(factors).map(([name,value]) => {
    const score = Math.round((value.normalized ?? 0) * 100);
    return <div className="factor" key={name}><div className="factor-head"><span>{name.replaceAll("_"," ")}</span><span>{score}/100 · {Math.round((value.weight ?? 0)*100)}%</span></div><div className="factor-track"><div className="factor-fill" style={{width:`${score}%`}} /></div></div>;
  }) : <p className="subtle">Factor detail will appear with the first official snapshot.</p>}</section>;
}
