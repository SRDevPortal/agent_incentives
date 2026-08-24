from agent_incentives.setup.custom_fields import ensure_custom_fields


def setup_all():
    ensure_custom_fields()


def after_install():
    setup_all()


def after_migrate():
    setup_all()
