import io
import re
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

import pandas as pd
import streamlit as st
from playwright.sync_api import sync_playwright

st.set_page_config(page_title="MAMUNIX Lead Scraper", page_icon="🚀", layout="centered")
st.title("🚀 MAMUNIX Google Maps Lead Scraper")
st.markdown("Enter a business type and the number of leads. The tool will generate an Excel file with phone numbers.")

with st.form("scraper_form"):
    search_query = st.text_input("Search Query", placeholder="e.g., Coffee shop in Dhaka")
    max_results = st.number_input("Number of Leads", min_value=1, max_value=100, value=10)
    show_browser = st.checkbox("Show browser window (unchecked = faster)", value=False)
    submit_btn = st.form_submit_button("Start Scraping")


def clean_phone(raw):
    return re.sub(r"[^\d+\s\-()]", "", raw or "").strip()


def build_excel(df):
    """Create a formatted Excel file in memory and return its bytes."""
    from openpyxl.styles import Font, PatternFill, Alignment

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")
        ws = writer.sheets["Leads"]

        header_fill = PatternFill("solid", fgColor="1F4E78")
        header_font = Font(bold=True, color="FFFFFF")
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Auto column width
        for col in ws.columns:
            max_len = max(len(str(c.value)) if c.value else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 3, 60)

        # Make website links clickable
        website_col = list(df.columns).index("Website") + 1
        for row in range(2, ws.max_row + 1):
            cell = ws.cell(row=row, column=website_col)
            if cell.value and str(cell.value).startswith("http"):
                cell.hyperlink = cell.value
                cell.font = Font(color="0563C1", underline="single")

        ws.freeze_panes = "A2"
    return buffer.getvalue()


def run_playwright_task(query, limit, headless):
    results, seen = [], set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(locale="en-US", viewport={"width": 1280, "height": 900})
        page = context.new_page()
        try:
            url = f"https://www.google.com/maps/search/{quote(query)}?hl=en"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Handle cookie consent page if it appears
            for label in ["Accept all", "Reject all"]:
                btn = page.locator(f"button:has-text('{label}')")
                if btn.count() > 0:
                    btn.first.click()
                    page.wait_for_load_state("domcontentloaded")
                    break

            page.wait_for_selector('div[role="feed"]', timeout=30000)
            feed = page.locator('div[role="feed"]')
            link_sel = 'a[href*="/maps/place/"]'

            # Scroll to load extra results (duplicates will be skipped later)
            target = limit * 2
            last_count, stalled = 0, 0
            for _ in range(40):
                count = page.locator(link_sel).count()
                if count >= target:
                    break
                if page.locator("text=You've reached the end of the list").is_visible():
                    break
                stalled = stalled + 1 if count == last_count else 0
                if stalled >= 4:
                    break
                last_count = count
                feed.evaluate("n => n.scrollTop = n.scrollHeight")
                time.sleep(1.5)

            total = page.locator(link_sel).count()

            for i in range(total):
                if len(results) >= limit:
                    break
                try:
                    item = page.locator(link_sel).nth(i)
                    name = item.get_attribute("aria-label") or "N/A"
                    item.scroll_into_view_if_needed()
                    item.click()

                    # Wait until the details panel shows THIS business
                    try:
                        page.wait_for_function(
                            """(n) => Array.from(document.querySelectorAll('h1'))
                                .some(h => h.innerText.trim().includes(n))""",
                            arg=name,
                            timeout=8000,
                        )
                    except Exception:
                        page.wait_for_selector("h1", timeout=5000)
                    time.sleep(1.2)

                    phone = "N/A"
                    loc = page.locator('button[data-item-id^="phone:tel:"]')
                    if loc.count() > 0:
                        phone = clean_phone(loc.first.get_attribute("aria-label")) or "N/A"

                    website = "N/A"
                    loc = page.locator('a[data-item-id="authority"]')
                    if loc.count() > 0:
                        website = loc.first.get_attribute("href") or "N/A"

                    address = "N/A"
                    loc = page.locator('button[data-item-id="address"]')
                    if loc.count() > 0:
                        address = (loc.first.get_attribute("aria-label") or "").replace("Address:", "").strip() or "N/A"

                    # Skip duplicate phone numbers (same phone = same business in practice)
                    key = phone if phone != "N/A" else (name, address)
                    if key in seen:
                        continue
                    seen.add(key)

                    results.append({
                        "Business Name": name,
                        "Phone Number": phone,
                        "Website": website,
                        "Address": address,
                    })
                except Exception as e:
                    print(f"Item {i} skipped: {e}")
                    continue

            return {"status": "success", "data": results}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            browser.close()


if submit_btn:
    if not search_query.strip():
        st.warning("Please enter a search query first!")
    else:
        with st.spinner(f"Scraping '{search_query}'... Please wait."):
            with ThreadPoolExecutor(max_workers=1) as ex:
                response = ex.submit(run_playwright_task, search_query, int(max_results), not show_browser).result()

        if response["status"] == "success" and response["data"]:
            df = pd.DataFrame(response["data"])
            safe_name = re.sub(r"[^\w\-]+", "_", search_query.strip())
            filename = f"{safe_name}_leads.xlsx"

            excel_data = build_excel(df)
            with open(filename, "wb") as f:
                f.write(excel_data)

            st.success(f"Done! Extracted {len(df)} unique leads and saved as '{filename}'.")
            if len(df) < int(max_results):
                st.info(f"Only {len(df)} unique leads were available for this search (you asked for {int(max_results)}).")
            st.dataframe(df)
            st.download_button(
                label="📥 Download Excel File",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        elif response["status"] == "error":
            st.error(f"Scraping failed: {response['message']}")
        else:
            st.warning("No results found. Try a different search query.")