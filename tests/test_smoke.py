from builders_first import paths


def test_paths_exist():
    assert paths.CACHE.exists()
