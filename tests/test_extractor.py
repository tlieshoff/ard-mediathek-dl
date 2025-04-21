import pytest
from ard_mediathek_dl.extractor import list_variants, choose_variant

# Using a sample master.m3u8 for testing — replace with mock URL or local file in real tests
MASTER_URL = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"

def test_list_variants_has_entries():
    variants = list_variants(MASTER_URL)
    assert isinstance(variants, list)
    assert all(len(item) == 2 for item in variants)

def test_choose_variant_best():
    selected = choose_variant(MASTER_URL, quality="best")
    assert selected.endswith(".m3u8")

def test_choose_variant_worst():
    selected = choose_variant(MASTER_URL, quality="worst")
    assert selected.endswith(".m3u8")
