from tasks.celery_app import celery
from tasks.batch_tasks import get_message


def test_celery_configuration():
    assert celery.conf.task_default_queue == "wormcat_web"
    assert celery.conf.broker_transport_options.get("global_keyprefix") == "wormcat_web:"


def test_get_message_timeout(mocker):
    # Mock redis brpop returning None on timeout
    mocker.patch("tasks.batch_tasks.redis_server.brpop", return_value=None)
    result = get_message("dummy_channel", timeout=1)
    assert result == {"name": "TIMEOUT", "value": 1}


def test_get_message_valid(mocker):
    # Mock redis brpop returning valid json tuple
    mocker.patch("tasks.batch_tasks.redis_server.brpop", return_value=(b"channel", b'{"name": "DONE", "value": "test_dir"}'))
    result = get_message("dummy_channel", timeout=1)
    assert result == {"name": "DONE", "value": "test_dir"}
