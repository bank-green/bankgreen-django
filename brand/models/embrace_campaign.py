from django.db import models
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from jsonschema import validate
from jsonschema.exceptions import ValidationError as JsonValidationError


def validate_configuration(json_config):
    configuration_schema = {
        "type": "object",
        "additionalProperties": True,
        "required": ["email", "system_prompt", "user_prompt"],
    }

    try:
        validate(instance=json_config, schema=configuration_schema)
    except JsonValidationError as error:
        raise ValidationError(error.message)

    try:
        validate_email(json_config["email"])
    except:
        raise ValidationError("Enter a valid email address")

    for key, value in json_config.items():
        if not value.strip():
            raise ValidationError(f"Enter a valid value for {key}")


class EmbraceCampaign(models.Model):
    name = models.CharField(max_length=40)
    description = models.TextField()
    configuration = models.JSONField(default=dict, validators=[validate_configuration])

    def __str__(self):
        return self.name
