from demo.config import Settings


def test_remote_host_has_no_repository_default():
    settings = Settings(_env_file=None)

    assert settings.harness1_remote_host is None
