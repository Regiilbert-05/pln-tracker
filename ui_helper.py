import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import streamlit as st
import streamlit.components.v1 as components

# Timezone Utility
LOCAL_TZ = ZoneInfo(os.environ.get("TZ", "Asia/Jakarta"))

def utc_to_local(dt):
    """Konversi datetime UTC ke waktu lokal"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(LOCAL_TZ)

def apply_custom_css():
    """Terapkan CSS modern untuk Light & Dark mode"""
    st.markdown("""
<style>
    /* Hilangkan spasi berlebih di atas halaman */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }
    
    /* Typography & Header */
    .app-title {
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        font-weight: 800;
        font-size: 1.85rem;
        letter-spacing: -0.02em;
        color: var(--text-color) !important;
        margin-bottom: 0.1rem;
    }
    .app-subtitle {
        color: var(--text-color) !important;
        opacity: 0.75;
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
    }
    
    /* Top Header Bar Container */
    .top-header-box {
        background-color: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.25) !important;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Form & Card Containers */
    .form-card {
        background-color: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.25) !important;
        border-radius: 14px;
        padding: 1.5rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
    }
    .card-header-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-color) !important;
        margin-bottom: 0.4rem;
    }
    .card-header-subtitle {
        font-size: 0.85rem;
        color: var(--text-color) !important;
        opacity: 0.75;
        margin-bottom: 1.2rem;
    }
    
    /* Metric Cards */
    .metric-box {
        background-color: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.25) !important;
        border-radius: 14px;
        padding: 1.2rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.12);
    }
</style>
""", unsafe_allow_html=True)

def inject_wheel_js():
    """Injeksi JS override scroll wheel dengan debouncing"""
    wheel_js_code = """
<script>
(function() {
    try {
        const parentDoc = window.parent ? window.parent.document : document;
        const parentWin = window.parent || window;

        if (parentWin.__wheelOverrideInitialized) return;
        parentWin.__wheelOverrideInitialized = true;

        const debounceTimers = new Map();

        parentDoc.addEventListener('wheel', function(e) {
            const container = e.target.closest('div[data-testid="stNumberInput"]');
            if (!container) return;

            const input = container.querySelector('input');
            if (!input) return;

            e.preventDefault();
            e.stopPropagation();

            let currentVal = parseFloat(input.value);
            if (isNaN(currentVal)) currentVal = 0;

            let stepAttr = input.getAttribute('step');
            let step = stepAttr ? parseFloat(stepAttr) : (input.value.includes('.') ? 0.1 : 1.0);
            if (isNaN(step) || step <= 0) step = 1.0;

            let minAttr = input.getAttribute('min');
            let maxAttr = input.getAttribute('max');
            let min = minAttr !== null ? parseFloat(minAttr) : null;
            let max = maxAttr !== null ? parseFloat(maxAttr) : null;

            let delta = e.deltaY < 0 ? step : -step;
            
            let decimals = 0;
            if (step.toString().includes('.')) {
                decimals = step.toString().split('.')[1].length;
            } else if (input.value.includes('.')) {
                decimals = input.value.split('.')[1].length;
            }
            
            let newVal = parseFloat((currentVal + delta).toFixed(Math.max(decimals, 0)));

            if (min !== null && newVal < min) newVal = min;
            if (max !== null && newVal > max) newVal = max;

            const key = input.name || input.id || 'default';
            
            if (debounceTimers.has(key)) {
                clearTimeout(debounceTimers.get(key));
            }
            
            debounceTimers.set(key, setTimeout(() => {
                try { input.focus(); } catch(e) {}
                
                const nativeSetter = Object.getOwnPropertyDescriptor(parentWin.HTMLInputElement.prototype, 'value').set;
                nativeSetter.call(input, newVal);

                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                
                input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
                input.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
                input.dispatchEvent(new Event('blur', { bubbles: true }));
            }, 300));
        }, { passive: false });
    } catch (err) {}
})();
</script>
"""
    if hasattr(st, "iframe"):
        st.iframe(wheel_js_code, height=1)
    else:
        components.html(wheel_js_code, height=0, width=0)
