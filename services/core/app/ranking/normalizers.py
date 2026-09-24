from __future__ import annotations
import math
from collections.abc import Callable
from statistics import median
Number=float|int|None
def _present(values:list[Number])->list[float]: return [float(v) for v in values if v is not None]
def _restore(values:list[Number],transform:Callable[[float],float])->list[float|None]:
    return [None if v is None else min(1.0,max(0.0,transform(float(v)))) for v in values]
def min_max(values:list[Number])->list[float|None]:
    p=_present(values)
    if not p:return [None]*len(values)
    lo,hi=min(p),max(p)
    if math.isclose(lo,hi): return _restore(values,lambda _v:1.0 if hi>0 else 0.0)
    return _restore(values,lambda v:(v-lo)/(hi-lo))
def log1p(values:list[Number])->list[float|None]:
    p=_present(values)
    if not p:return [None]*len(values)
    high=max(math.log1p(max(0.0,v)) for v in p)
    if math.isclose(high,0.0): return _restore(values,lambda _v:0.0)
    return _restore(values,lambda v:math.log1p(max(0.0,v))/high)
def percentile(values:list[Number])->list[float|None]:
    p=_present(values)
    if not p:return [None]*len(values)
    if len(p)==1:return _restore(values,lambda _v:1.0)
    ordered=sorted(p)
    def pct(v:float)->float:
        idx=[i for i,x in enumerate(ordered) if math.isclose(x,v)]; return (sum(idx)/len(idx))/(len(ordered)-1)
    return _restore(values,pct)
def robust_z(values:list[Number])->list[float|None]:
    p=_present(values)
    if not p:return [None]*len(values)
    c=median(p); mad=median([abs(v-c) for v in p])
    if math.isclose(mad,0): return _restore(values,lambda v:0.5 if math.isclose(v,c) else (1.0 if v>c else 0.0))
    return _restore(values,lambda v:1/(1+math.exp(-max(-30,min(30,0.67448975*(v-c)/mad)))))
def capped_min_max(values:list[Number])->list[float|None]:
    p=sorted(_present(values))
    if not p:return [None]*len(values)
    cap=p[max(0,math.ceil(.95*len(p))-1)]; lo=min(p)
    if math.isclose(lo,cap):return _restore(values,lambda _v:1.0 if cap>0 else 0.0)
    return _restore(values,lambda v:(min(v,cap)-lo)/(cap-lo))
NORMALIZERS={'log1p':log1p,'percentile':percentile,'robust_z':robust_z,'min_max':min_max,'capped_min_max':capped_min_max}
def normalize(method:str,values:list[Number])->list[float|None]:
    try:return NORMALIZERS[method](values)
    except KeyError as exc: raise ValueError(f'Unknown normalization method: {method}') from exc
