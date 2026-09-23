"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type Point = { ranking:string; quarter:string; rank:number; score:number };

export function RankHistoryChart({ points }: { points: Point[] }) {
  const navigate = (point: Point) => {
    window.location.href = `/technology/${point.ranking}?quarter=${encodeURIComponent(point.quarter)}`;
  };
  return <section className="chart-wrap">
    <h2 className="chart-title">Rank history</h2>
    <div style={{width:"100%",height:260}} aria-hidden="true">
      <ResponsiveContainer><LineChart data={points} margin={{top:8,right:10,left:-25,bottom:8}}>
        <XAxis dataKey="quarter" stroke="#9fb9aa" fontSize={11}/><YAxis reversed allowDecimals={false} stroke="#9fb9aa" fontSize={11}/><Tooltip />
        <Line type="monotone" dataKey="rank" stroke="#7cf2a8" strokeWidth={3} dot={{r:4,cursor:"pointer"}} activeDot={(props:any) => <circle {...props} r={7} fill="#ffd66b" onClick={() => navigate(points[props.index])} style={{cursor:"pointer"}}/>}/>
      </LineChart></ResponsiveContainer>
    </div>
    <table className="sr-table"><thead><tr><th>Quarter</th><th>Rank</th><th>Score</th></tr></thead><tbody>{points.map(point => <tr key={`${point.ranking}-${point.quarter}`}><td>{point.quarter}</td><td>#{point.rank}</td><td>{point.score.toFixed(1)}</td></tr>)}</tbody></table>
  </section>;
}
