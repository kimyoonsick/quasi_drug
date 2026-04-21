import asyncio
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scrapers.saeropharm_scraper import SaeropharmEventScraper

async def check():
    s = SaeropharmEventScraper()
    await s.start_browser(headless=False)
    await s.login()
    await s.page.goto(s.EVENT_URL, wait_until="networkidle")
    
    from scrapers.bot_helper import human_delay, human_scroll
    await human_delay(2,3)
    await human_scroll(s.page)
    
    events = await s.page.evaluate("""() => {
        // Find elements that look like events
        let container = document.querySelector('.event_list, .evt_list, .board_list, .list_wrap, ul.list, .event_zone');
        if (!container) {
            // Find container of first img that has alt with '이벤트' or similar
            const imgs = Array.from(document.querySelectorAll('img')).filter(i => {
                const src = i.src || '';
                const alt = i.alt || '';
                return src.includes('event') || src.includes('cate') || alt.includes('이벤트');
            });
            if (imgs.length > 0) {
                container = imgs[0].closest('ul, .wrap, .list');
            }
        }
        
        if (!container) return { error: "No container found", outerHTML: document.body.innerHTML.substring(0, 1000) };
        
        const items = Array.from(container.querySelectorAll('li, .item, .box'));
        const results = [];
        
        for (const el of items) {
            const a = el.querySelector('a');
            const img = el.querySelector('img');
            
            let html = el.outerHTML;
            if (html.length > 500) html = html.substring(0, 500) + "...";
            
            results.push({
                a_href: a ? a.href : null,
                a_onclick: a ? a.getAttribute('onclick') : null,
                img_src: img ? img.src : null,
                img_alt: img ? img.alt : null,
                html: html
            });
        }
        return { container_class: container.className, items: results };
    }""")
    
    print(events)
    await s.stop_browser()

asyncio.run(check())
