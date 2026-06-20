from importlib.metadata import version


def test_google_genai_sdk_is_available_with_supported_major_version():
    installed_version = version("google-genai")

    assert installed_version.split(".", maxsplit=1)[0] == "2"

    from google import genai

    assert callable(genai.Client)
