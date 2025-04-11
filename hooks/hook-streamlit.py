# hooks/hook-streamlit.py

from PyInstaller.utils.hooks import copy_metadata

# This hook ensures Streamlit's metadata is copied correctly
datas = copy_metadata("streamlit")
print(f"[Hook] Copied metadata for Streamlit: {datas}")  # Add print for confirmation
