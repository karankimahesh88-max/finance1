"""
Cached Supabase client. @st.cache_resource means this only runs once per
server process, not on every Streamlit rerun.

Requires .streamlit/secrets.toml:

    supabase_url = "https://xxxxxxxxxxxx.supabase.co"
    supabase_anon_key = "eyJhbGciOi..."
"""
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_client() -> Client:
    return create_client(st.secrets["supabase_url"], st.secrets["supabase_anon_key"])
