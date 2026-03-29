"""
isg/__init__.py
===============
Flask Blueprint kaydı.
panel.py'ye sadece şu 3 satır eklenir:

    try:
        from isg import isg_blueprint
        app.register_blueprint(isg_blueprint, url_prefix='/panel/isg')
    except Exception as e:
        logger.warning(f"ISG modülü yüklenemedi: {e}")
"""

from flask import Blueprint

isg_blueprint = Blueprint(
    "isg",
    __name__,
    template_folder="templates"
)

# Route'ları yükle
from isg import panel_routes  # noqa: F401, E402
