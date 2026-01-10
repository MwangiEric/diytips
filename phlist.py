import streamlit as st, requests, time, json, os
from bs4 import BeautifulSoup
import vercel_blob  # Ensure BLOB_READ_WRITE_TOKEN is in your environment

SEARX = "https://far-paule-emw-a67bd497.koyeb.app/search"

def searx_first_hit(query: str):
    try:
        res = requests.get(SEARX, params={"q": f"{query} site:gsmarena.com", "format": "json"}, timeout=15)
        return res.json().get("results", [])[0] # Return the first hit
    except: return None

def get_image_2_url(url: str):
    try:
        page = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(page.text, "lxml")
        h2 = soup.select_one("#pictures-list h2")
        imgs = []
        if h2:
            for tag in h2.find_next_siblings("img"):
                src = tag.get("src", "")
                if src:
                    if src.startswith("//"): src = "https:" + src
                    elif not src.startswith("http"): src = "https://www.gsmarena.com/" + src
                    imgs.append(src)
        return imgs[1] if len(imgs) >= 2 else None
    except: return None

# ---------- STREAMLIT UI ----------
st.title("☁️ Vercel Blob Porter")
st.info("Uploads SearXNG JSON + Image #2 to Vercel.")

models = st.text_area("Phone models", value="Google Pixel 9\niPhone 16")

if st.button("Process & Upload"):
    jobs = [m.strip() for m in models.splitlines() if m.strip()]
    bar = st.progress(0)

    for idx, model in enumerate(jobs):
        device_id = model.lower().replace(" ", "-")
        st.write(f"🔄 Processing **{model}**...")

        # 1. Fetch Data
        hit = searx_first_hit(model)
        if not hit: continue
        
        img_url = get_image_2_url(hit["url"])

        # 2. Upload JSON to Vercel Blob
        try:
            json_data = json.dumps(hit, indent=2)
            vercel_blob.put(f"phones/{device_id}/data.json", json_data, {"access": "public"})
            st.write(f"  ✅ JSON uploaded")
        except Exception as e:
            st.error(f"  ❌ JSON Upload fail: {e}")

        # 3. Upload Image 2 to Vercel Blob
        if img_url:
            try:
                img_bytes = requests.get(img_url).content
                vercel_blob.put(f"phones/{device_id}/image_2.jpg", img_bytes, {"access": "public"})
                st.write(f"  ✅ Image #2 uploaded")
            except Exception as e:
                st.error(f"  ❌ Image Upload fail: {e}")
        
        bar.progress((idx + 1) / len(jobs))
        time.sleep(1)

    st.success("All uploads completed!")
