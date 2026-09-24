from app.ranking.normalizers import normalize
def test_normalizers_are_deterministic_and_bounded():
    v=[0.,1.,10.,100.]
    for m in ['log1p','percentile','robust_z','min_max','capped_min_max']:
        a=normalize(m,v); assert a==normalize(m,v); assert all(0<=x<=1 for x in a if x is not None)
def test_missing_values_are_preserved():
    r=normalize('min_max',[1.,None,3.]); assert r[1] is None; assert r[0]==0; assert r[2]==1
