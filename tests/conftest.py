import pytest
from db import DatabaseManager


@pytest.fixture
def sample_html() -> str:
    return """
    <div>
      <div class="card">
        <a href="/p/botol-minum-corkcicle-16oz-1399887766/?t-id=abc">
          <img src="https://media.karousell.com/media/photos/products/botol.jpg" />
          <span>@penjual_amanah</span>
          <span>5 menit lalu</span>
          <p>Botol Minum Corkcicle 16oz Original</p>
          <p>Rp 250.000</p>
          <p>Seperti baru</p>
        </a>
      </div>
      <div class="card">
        <a href="/p/botol-tupperware-1l-1399887799/">
          <span>@toko_botol</span>
          <span>1 jam lalu</span>
          <p>Botol Tupperware 1L Biru</p>
          <p>Rp 50.000</p>
          <p>Baru</p>
        </a>
      </div>
    </div>
    """


@pytest.fixture
def temp_db(tmp_path) -> DatabaseManager:
    db_file = tmp_path / "test_carousell.db"
    return DatabaseManager(db_path=str(db_file))