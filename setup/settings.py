from pathlib import Path


# APPS
apps = [
    "pwNFSe",
    "ordens",
    "sapNFSe",
]

# DIRETORIOS
BASE_DIR = Path(__file__).parent.parent
DIRS = {
    'DIR_NFSE': {
        'NFSE_DOWNLOAD': str(BASE_DIR / 'files' / 'nfse_download'),
        'NFSE_ACCEPT': str(BASE_DIR / 'files' / 'nfse_accept'),
        'NFSE_REJECT': str(BASE_DIR / 'files' / 'nfse_reject'),
    },
}

# --- THEMAS CORES TEMA ---
# DARK
theme_mode = {
    'DARK': {
        'BG_BAR':"#333333",
        'BG_SIDEBAR': "#1e1e1e",
        'BG_EDITOR':"#121212",
        'ACCENT_COLOR':"#007acc",
        'ICON_COLOR':'gray',
        'TEXT_PRIMARY': 'white',
    },
    'LIGHT': {
        'BG_BAR': "#f3f3f3",
        'BG_SIDEBAR': "#f3f3f3",
        'BG_EDITOR':"#ffffff",
        'ACCENT_COLOR':"#005fb8",
        'ICON_COLOR':'black',
        'TEXT_PRIMARY': '#333333',
    }
}

