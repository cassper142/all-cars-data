import asyncio
import json
import argparse
from playwright.async_api import async_playwright

async def handle_route(route):
    # Блокируем всё лишнее: картинки, стили, шрифты
    if route.request.resource_type != "document":
        await route.abort()
    else:
        await route.continue_()

async def main(cfg):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        await context.route("**/*", handle_route)
        page = await context.new_page()

        print(">>> Собираем список брендов...")
        await page.goto("https://www.cars-data.com/en/all-cars.html", wait_until="domcontentloaded")
        
        brands_list = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('.footerbrands a'))
                .map(a => ({ name: a.innerText.trim(), url: a.href }));
        }""")

        if cfg.max_brands: brands_list = brands_list[:cfg.max_brands]

        full_tree = []

        for b in brands_list:
            brand_obj = {"brand": b['name'], "models": []}
            print(f"\n[v] БРЕНД: {b['name']}")
            
            try:
                await page.goto(b['url'], wait_until="domcontentloaded")
                model_links = await page.evaluate(f"""() => {{
                    const links = Array.from(document.querySelectorAll('a'))
                        .filter(a => a.href.includes('{b['url']}/') && !a.href.includes('.html'))
                        .map(a => ({{ name: a.innerText.trim(), url: a.href }}));
                    return Object.values(links.reduce((acc, curr) => {{
                        if (curr.name && !curr.name.includes('Cars-Data')) acc[curr.url] = curr;
                        return acc;
                    }}, {{}}));
                }}""")

                for m in model_links:
                    model_obj = {"model": m['name'], "generations": []}
                    print(f"  [*] Модель: {m['name']}")
                    
                    await page.goto(m['url'], wait_until="domcontentloaded")
                    generations = await page.evaluate("""() => {
                        return Array.from(document.querySelectorAll('a'))
                            .filter(a => /\\/\\d+$/.test(a.href))
                            .map(a => ({ name: a.innerText.trim().split('\\n')[0], url: a.href }));
                    }""")

                    for gen in generations:
                        print(f"    [-] Ген: {gen['name']}")
                        await page.goto(gen['url'], wait_until="domcontentloaded")
                        
                        modifications = await page.evaluate("""() => {
                            return Array.from(document.querySelectorAll('a'))
                                .filter(a => a.href.includes('-specs/'))
                                .map(a => a.innerText.trim());
                        }""")
                        
                        model_obj["generations"].append({
                            "generation": gen['name'],
                            "modifications": sorted(list(set(modifications)))
                        })
                    
                    brand_obj["models"].append(model_obj)
                
                full_tree.append(brand_obj)

            except Exception as e:
                print(f"  [ERR] Ошибка на {b['name']}: {e}")

        # Финальное сохранение в красивом формате
        print(f"\n>>> Сохранение в {cfg.output_path}...")
        with open(cfg.output_path, "w", encoding="utf-8") as f:
            json.dump(full_tree, f, ensure_ascii=False, indent=4)
        
        print(">>> Готово.")
        await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", dest="output_path", default="car_tree_pretty.json")
    parser.add_argument("--max-brands", type=int, default=0)
    args = parser.parse_args()
    asyncio.run(main(args))