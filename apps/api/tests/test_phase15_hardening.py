from concurrent.futures import ThreadPoolExecutor
from time import perf_counter

import pytest
from sqlalchemy import create_engine
from test_phase4_inventory import StockLine, ctx, post, seed
from test_phase12_finance import setup_finance

from app.application.hardening import reconciliation_snapshot
from app.core.config import get_settings


@pytest.fixture
def engine():
    url=get_settings().database_url
    if not url.startswith("postgresql"): pytest.skip("Phase 15 acceptance requires PostgreSQL")
    value=create_engine(url,pool_pre_ping=True)
    try: yield value
    finally: value.dispose()


def test_four_core_reconciliation_baseline(engine):
    tenant,*_=seed(engine)
    with engine.begin() as db:
        snap=reconciliation_snapshot(db,tenant_id=tenant)
        assert snap["healthy"] is True
        assert snap["inventory_quantity_variance"]=="0"
        assert snap["unbalanced_journals"]==0
        assert snap["duplicate_financial_sources"]==0


def test_reconciliation_read_smoke_p95_under_pilot_target(engine):
    tenant,*_=seed(engine)
    timings=[]
    with engine.connect() as db:
        for _ in range(40):
            started=perf_counter();reconciliation_snapshot(db,tenant_id=tenant);timings.append((perf_counter()-started)*1000)
    timings.sort();p95=timings[int(len(timings)*0.95)-1]
    assert p95<750


def test_concurrent_inventory_never_oversells(engine):
    tenant,entity,branch,unit,product,location,*_=seed(engine)
    context=ctx(tenant)
    post(engine,context,entity,branch,"RECEIVE",StockLine(product,unit,location,None,"5"),"phase15-load-seed")
    def issue(key):
        try:
            return post(engine,context,entity,branch,"ISSUE",StockLine(product,unit,location,None,"4"),key)
        except ValueError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(issue,["phase15-c1","phase15-c2"]))
    assert sum(x is not None for x in results)==1


def test_finance_setup_still_balanced_under_hardening(engine):
    tenant,*_=setup_finance(engine)
    with engine.begin() as db:
        snap=reconciliation_snapshot(db,tenant_id=tenant)
        assert snap["healthy"] is True
