from django.core.files.uploadedfile import SimpleUploadedFile

from jobs.forms import ResumeUploadForm, SignUpForm


def test_signup_requires_letters_and_numbers(db):
    form = SignUpForm(
        {
            "username": "student",
            "email": "",
            "password1": "onlyletters",
            "password2": "onlyletters",
        }
    )

    assert not form.is_valid()
    assert "字母和数字" in form.errors["password1"][0]


def test_resume_form_rejects_extension_and_large_file(db):
    wrong_extension = ResumeUploadForm(files={"file": SimpleUploadedFile("resume.txt", b"text")})
    too_large = ResumeUploadForm(
        files={
            "file": SimpleUploadedFile(
                "resume.pdf",
                b"x" * (ResumeUploadForm.MAX_FILE_SIZE + 1),
                content_type="application/pdf",
            )
        }
    )

    assert not wrong_extension.is_valid()
    assert "PDF" in wrong_extension.errors["file"][0]
    assert not too_large.is_valid()
    assert "5 MB" in too_large.errors["file"][0]
