import os
import shutil
import tempfile
import pytest
from jinja2.exceptions import SecurityError
from semversioner import Semversioner

@pytest.fixture
def directory_name():
    dir_name = tempfile.mkdtemp()
    yield dir_name
    shutil.rmtree(dir_name)

def test_generate_changelog_ssti_protection(directory_name: str) -> None:
    """
    Test that the changelog generation is protected against SSTI.
    """
    releaser = Semversioner(path=directory_name)

    # Payload attempting to access unsafe attributes
    payload = "{{ self.__init__.__globals__['__builtins__'] }}"

    with pytest.raises(SecurityError) as excinfo:
        releaser.generate_changelog(template=payload)

    assert "access to attribute '__init__' of 'TemplateReference' object is unsafe" in str(excinfo.value)

def test_generate_changelog_safe_template(directory_name: str) -> None:
    """
    Test that a normal, safe template still works.
    """
    releaser = Semversioner(path=directory_name)
    releaser.add_change("minor", "Safe change")
    releaser.release()

    template = "Version: {{ current_version }}"
    result = releaser.generate_changelog(template=template)

    assert "Version: 0.1.0" in result
