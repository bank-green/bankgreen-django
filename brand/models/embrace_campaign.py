from django.db import models
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


def validate_configuration(json_config):
    schema_keys = ["email", "system_prompt", "user_prompt"]
    schema_default_values = [
        "write email address here",
        "Write the system instructions here",
        "write your question here",
    ]

    unknown_keys = set(json_config.keys()) - set(schema_keys)
    if unknown_keys:
        raise ValidationError(
            f"Acceptable keys are {schema_keys}. \
                              {unknown_keys} should not be present."
        )

    try:
        validate_email(json_config["email"])
    except:
        raise ValidationError("Enter a valid email address")

    for key in schema_keys[1:]:
        value = json_config[key]
        if not value.strip() or (value in schema_default_values):
            raise ValidationError(f"Enter a valid value for {key}")


class EmbraceCampaign(models.Model):
    name = models.CharField(max_length=40)
    description = models.TextField()
    configuration = models.JSONField(default=dict, validators=[validate_configuration])

    def __str__(self):
        return self.name
