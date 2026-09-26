import { ImageResponse } from "next/og";
import { apiGet, type ShareMetadata } from "../../../../lib/api";

const sizes = {
  square: { width: 1080, height: 1080 },
  portrait: { width: 1080, height: 1350 },
  story: { width: 1080, height: 1920 },
  landscape: { width: 1200, height: 630 },
} as const;

type Format = keyof typeof sizes;

export async function GET(request: Request, { params }: { params: Promise<{ rankingResultId: string }> }) {
  const { rankingResultId } = await params;
  const url = new URL(request.url);
  const requested = url.searchParams.get("format") ?? "square";
  const format: Format = requested in sizes ? requested as Format : "square";
  let data: ShareMetadata;
  try { data = await apiGet<ShareMetadata>(`/v1/rankings/results/${rankingResultId}/share`); }
  catch { return new Response("Published ranking result not found", { status: 404 }); }
  const movement = data.movement == null ? "NEW" : data.movement > 0 ? `↑ ${data.movement}` : data.movement < 0 ? `↓ ${Math.abs(data.movement)}` : "—";
  const response = new ImageResponse(
    <div style={{width:"100%",height:"100%",display:"flex",flexDirection:"column",justifyContent:"space-between",background:"#07120d",color:"#f5fff9",padding:"72px",fontFamily:"sans-serif"}}>
      <div style={{display:"flex",justifyContent:"space-between",fontSize:28,fontWeight:800}}><span>TOPTENUG 🇺🇬</span><span style={{color:"#7cf2a8"}}>{data.quarter}</span></div>
      <div style={{display:"flex",flexDirection:"column"}}><span style={{color:"#9fb9aa",fontSize:28,textTransform:"uppercase",letterSpacing:4}}>{data.category.replaceAll("-"," ")}</span><span style={{fontSize:210,fontWeight:900,lineHeight:1,letterSpacing:-14}}>#{data.rank}</span><span style={{fontSize:60,fontWeight:800,marginTop:24}}>{data.name}</span><span style={{fontSize:30,color:"#7cf2a8",marginTop:20}}>{movement} this quarter · score {data.score.toFixed(1)}</span></div>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"end",fontSize:24,color:"#9fb9aa"}}><span>{data.algorithm_name} {data.algorithm_version}<br/>Evidence-driven. Reproducible.</span><span>TopTenUG</span></div>
    </div>,
    sizes[format],
  );
  if (url.searchParams.get("download") === "1") response.headers.set("Content-Disposition", `attachment; filename="toptenug-${data.slug}-${data.quarter}-${format}.png"`);
  return response;
}
