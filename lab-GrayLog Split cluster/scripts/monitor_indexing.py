#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, shutil, sys, time, urllib.request
from collections import deque
from datetime import datetime

BLOCKS = " ▁▂▃▄▅▆▇█"

def args():
    p=argparse.ArgumentParser(description="Monitor terminal de indexación ES/OS")
    p.add_argument('--url', required=True)
    p.add_argument('--label', default='CLUSTER')
    p.add_argument('--interval', type=int, default=60)
    p.add_argument('--samples', type=int, default=30)
    p.add_argument('--index', default='_all')
    p.add_argument('--timeout', type=float, default=5.0)
    return p.parse_args()

def total(url, index, timeout):
    endpoint=f"{url.rstrip('/')}/{index}/_stats/indexing"
    req=urllib.request.Request(endpoint, headers={'Accept':'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data=json.load(r)
    return int(data['_all']['primaries']['indexing']['index_total'])

def spark(values):
    if not values: return ''
    m=max(values)
    if m<=0: return BLOCKS[0]*len(values)
    return ''.join(BLOCKS[round((v/m)*(len(BLOCKS)-1))] for v in values)

def clear():
    sys.stdout.write('\033[2J\033[H'); sys.stdout.flush()

def rate(delta, interval):
    return f"{delta/interval:,.2f} docs/s | {delta*60/interval:,.0f} docs/min"

def render(a, values, times, current, status):
    clear()
    width=shutil.get_terminal_size((100,30)).columns
    title=f"{a.label} :: operaciones de indexación"
    print(title); print('='*min(len(title),width))
    print(f"Cluster : {a.url}")
    print(f"Índices : {a.index}")
    print(f"Muestra : cada {a.interval}s | visibles: {a.samples}")
    print(f"Estado  : {status}")
    print(f"Total   : {current:,}\n")
    if not values:
        print('Esperando la primera diferencia entre muestras...')
        return
    vals=list(values)
    print(f"Actual  : {vals[-1]:,} operaciones | {rate(vals[-1],a.interval)}")
    print(f"Máximo  : {max(vals):,} operaciones por muestra")
    print(f"Promedio: {sum(vals)/len(vals):,.1f} operaciones por muestra\n")
    print(spark(vals)); print()
    print(f"Desde   : {times[0]}")
    print(f"Hasta   : {times[-1]}\n")
    print('Últimas muestras:')
    for t,v in zip(list(times)[-10:], vals[-10:]):
        print(f"  {t}  {v:>10,}  {rate(v,a.interval)}")
    print('\nCtrl+C para salir.')

def main():
    a=args()
    if a.interval<=0 or a.samples<=0:
        print('interval y samples deben ser > 0', file=sys.stderr); return 2
    values=deque(maxlen=a.samples); times=deque(maxlen=a.samples)
    try: previous=total(a.url,a.index,a.timeout)
    except Exception as e:
        print(f"No se pudo obtener la muestra inicial: {e}", file=sys.stderr); return 1
    render(a,values,times,previous,'conectado; esperando siguiente muestra')
    next_sample=time.monotonic()+a.interval
    try:
        while True:
            time.sleep(max(0,next_sample-time.monotonic())); next_sample+=a.interval
            try:
                current=total(a.url,a.index,a.timeout)
                delta=current-previous
                if delta<0:
                    previous=current
                    render(a,values,times,current,'contador reiniciado; nueva línea base')
                    continue
                previous=current; values.append(delta); times.append(datetime.now().strftime('%H:%M:%S'))
                render(a,values,times,current,'OK')
            except Exception as e:
                render(a,values,times,previous,f'ERROR: {e}')
    except KeyboardInterrupt:
        print('\nMonitor detenido.'); return 0

if __name__=='__main__':
    raise SystemExit(main())