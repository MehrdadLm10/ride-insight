"""Playwright runs solely inside a worker thread; GUI updates use a queue."""
import hashlib
import json
import re
import time
from collections import defaultdict
from dataclasses import asdict
from core import parse_card,infer_dates,save_xlsx
from providers import PROVIDERS

def run(provider,output,anchor,events,ready,stop):
    cards={};rides=[];reason='استخراج متوقف شد';browser=None
    try:
        from playwright.sync_api import sync_playwright
        config=PROVIDERS[provider]
        with sync_playwright() as p:
            try:
                browser=p.chromium.launch(channel='chrome',headless=False,args=['--start-maximized'])
                page=browser.new_page(no_viewport=True)
                page.goto(config['URL'],wait_until='domcontentloaded',timeout=60000)
                events.put(('login','وارد حساب شوید و تاریخچه سفرها را باز کنید؛ سپس «ورود انجام شد» را بزنید.'))
                while not ready.is_set():
                    if stop.is_set():return
                    if page.is_closed():raise RuntimeError('مرورگر بسته شد')
                    page.wait_for_timeout(200)
                if stop.is_set():return
                # Preserve the exact history page the user opened.
                events.put(('progress','خواندن سفرها آغاز شد'))
                idle_since=None;no_cards_since=time.monotonic();last_save=0
                for step in range(10000):
                    if stop.is_set():reason='توقف دستی؛ خروجی ممکن است ناقص باشد';break
                    before=len(cards);occ=defaultdict(int)
                    for card in page.evaluate(config['EXTRACT']):
                        key=hashlib.sha256(card['text'].encode()).hexdigest();occ[key]+=1
                        cards[f'{key}:{occ[key]}']=card
                    if len(cards)>before:
                        no_cards_since=time.monotonic()
                        events.put(('progress',f'{len(cards):,} کارت خوانده شد'))
                    if not cards and time.monotonic()-no_cards_since>20:
                        raise RuntimeError('کارتی پیدا نشد؛ تاریخچه سفرها را باز کنید و دوباره اجرا کنید.')
                    clicked=False
                    if len(cards)==before:
                        more=page.get_by_role('button',name=re.compile(r'^(نمایش بیشتر|بارگذاری بیشتر|سفرهای بیشتر|نمایش سفرهای بیشتر|بارگذاری سفرهای بیشتر|مشاهده سفرهای بیشتر|Load more|Show more)$',re.I))
                        for button in more.all():
                            if button.is_visible() and button.is_enabled():
                                button.click(timeout=5000);clicked=True;break
                    progress=page.evaluate(config['SCROLL'])
                    now=time.monotonic()
                    if len(cards)>before or progress['moved'] or not progress['bottom'] or clicked:
                        if idle_since is not None:events.put(('progress',f'بارگذاری سفرهای قدیمی‌تر ادامه دارد • {len(cards):,} کارت'))
                        idle_since=None
                    elif idle_since is None:
                        idle_since=now
                    if cards and idle_since is not None:
                        remaining=max(0,20-int(now-idle_since))
                        events.put(('progress',f'آماده‌سازی خروجی اکسل و گزارش آغاز شد • بررسی پایان تاریخچه: {remaining} ثانیه'))
                    if cards and now-last_save>=20:
                        rides=infer_dates([parse_card(c,provider,int(k.rsplit(':',1)[1])) for k,c in cards.items()],anchor)
                        output.with_suffix('.json').write_text(json.dumps(list(cards.values()),ensure_ascii=False,indent=2),encoding='utf-8')
                        try:save_xlsx(output,rides,anchor,'ذخیره موقت؛ استخراج ادامه دارد')
                        except PermissionError:events.put(('progress','اکسل باز است؛ آن را ببندید تا ذخیره شود. نسخه JSON محفوظ است.'))
                        last_save=now
                    if idle_since is not None and now-idle_since>=20:
                        reason='۲۰ ثانیه بدون پیشرفت در انتهای صفحه؛ کامل بودن تاریخچه تأیید نشده';break
                    page.wait_for_timeout(800)
                else:reason='سقف پیمایش؛ خروجی ناقص است'
            finally:
                if cards:
                    events.put(('progress','ذخیره‌سازی نهایی اکسل و آماده‌سازی گزارش آغاز شد…'))
                    rides=infer_dates([parse_card(c,provider,int(k.rsplit(':',1)[1])) for k,c in cards.items()],anchor)
                    output.with_suffix('.json').write_text(json.dumps(list(cards.values()),ensure_ascii=False,indent=2),encoding='utf-8')
                    try:save_xlsx(output,rides,anchor,reason)
                    except PermissionError:
                        output=output.with_name(output.stem+'_saved.xlsx');save_xlsx(output,rides,anchor,reason)
                    events.put(('data',(rides,str(output),reason)))
                if browser:
                    try:browser.close()
                    except Exception:pass
    except Exception as e:events.put(('error',f'{type(e).__name__}: {e}'))
    finally:events.put(('finished',None))
