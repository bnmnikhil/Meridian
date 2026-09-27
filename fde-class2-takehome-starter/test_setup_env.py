import pytest

import setup_env


def test_setup_env_writes_project_scoped_key_without_printing_it(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(setup_env, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(setup_env, "getpass", lambda prompt: "test-secret-key")
    monkeypatch.setattr("builtins.input", lambda prompt: "")

    setup_env.main()

    destination = tmp_path / ".env"
    assert destination.read_text(encoding="utf-8") == (
        "APP_OPENROUTER_API_KEY=test-secret-key\n"
        "APP_OPENROUTER_MODEL=openrouter/free\n"
    )
    output = capsys.readouterr().out
    assert "test-secret-key" not in output
    assert "key was not printed" in output


def test_setup_env_rejects_empty_key(tmp_path, monkeypatch):
    monkeypatch.setattr(setup_env, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(setup_env, "getpass", lambda prompt: "")
    monkeypatch.setattr("builtins.input", lambda prompt: "")

    with pytest.raises(SystemExit, match="No key was entered"):
        setup_env.main()
    assert not (tmp_path / ".env").exists()


def test_setup_env_does_not_replace_existing_file_without_confirmation(
    tmp_path, monkeypatch, capsys
):
    destination = tmp_path / ".env"
    destination.write_text("existing", encoding="utf-8")
    monkeypatch.setattr(setup_env, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr("builtins.input", lambda prompt: "no")

    setup_env.main()

    assert destination.read_text(encoding="utf-8") == "existing"
    assert "No changes made" in capsys.readouterr().out
