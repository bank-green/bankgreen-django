from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from brand.models import Brand
from brand.models.embrace_campaign import EmbraceCampaign


class RatingChoice(models.TextChoices):
    GREAT = "great"
    GOOD = "good"
    OK = "ok"
    BAD = "bad"
    WORST = "worst"
    UNKNOWN = "unknown"
    INHERIT = "inherit"


class EmbraceChoices(models.TextChoices):
    BREAKUP_LETTER = "breakup letter"
    NONE = "none"


class InstitutionType(models.Model):
    name = models.CharField(max_length=50, blank=False)
    description = models.CharField(
        max_length=100, blank=True, help_text="description for internal use"
    )

    def __str__(self):
        return self.name


class InstitutionCredential(models.Model):
    name = models.CharField(max_length=50, blank=False)
    description = models.CharField(
        max_length=100, blank=True, help_text="description for internal use"
    )
    prismic_api_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="the associated prismic API ID. Must match perfectly with the SFIDefaults type related image field. e.g. institution_credentials-gabv'",
    )

    def __str__(self):
        return self.name


class Commentary(models.Model):
    # Metadata
    brand = models.OneToOneField(
        Brand,
        related_name="commentary",
        help_text="What brand is this comment associated with?",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ["brand"]

    inherit_brand_rating = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inherit_brand_rating",
        help_text="should this brand have a rating inherited from another? If so, save will override the existing rating using the parent's rating unless the parent rating is blank.",
    )

    display_on_website = models.BooleanField(default=False)
    number_of_requests = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    comment = models.TextField(help_text="Meta. Comments for staff and/or editors", blank=True)
    rating = models.CharField(
        max_length=8,
        null=False,
        blank=False,
        choices=RatingChoice.choices,
        default=RatingChoice.UNKNOWN,
    )
    top_pick = models.BooleanField(default=False, help_text="Is this brand a top pick?")

    embrace_campaign = models.ManyToManyField(EmbraceCampaign, blank=True)

    @property
    def rating_inherited(self):
        return self.compute_inherited_rating()

    def compute_inherited_rating(self, inheritance_set=None, throw_error=False):

        inheritance_set = set() if inheritance_set is None else inheritance_set
        brand_in_inheritance_set = self.brand.tag in inheritance_set

        if throw_error and brand_in_inheritance_set:
            raise ValidationError(
                "Commentary rating is inherited from itself. Please assign a non-inherited rating."
            )
        elif not throw_error and brand_in_inheritance_set:
            return RatingChoice.UNKNOWN
        elif self.rating == RatingChoice.INHERIT and not self.inherit_brand_rating:
            return RatingChoice.UNKNOWN
        elif self.rating == RatingChoice.INHERIT and self.inherit_brand_rating:
            inheritance_set.add(self.brand.tag)
            return self.inherit_brand_rating.commentary.compute_inherited_rating(
                inheritance_set, throw_error=throw_error
            )

        return self.rating

    fossil_free_alliance = models.BooleanField(
        default=False, help_text="Is this brand in the fossil free alliance?"
    )

    # Deprecated. may be deleted later
    fossil_free_alliance_rating = models.IntegerField(
        blank=False,
        null=False,
        default=-1,
        help_text="the fossil free alliance rating. Values between -1 and 5. 0 for unknown rating. -1 for not FFA",
        validators=[MinValueValidator(-1), MaxValueValidator(5)],
    )

    # Negative Commentary

    amount_financed_since_2016 = models.CharField(
        max_length=150,
        help_text="Negative. Amount of fossil fuel investment the brand has financed since the paris accord, i.e. $382 billion USD",
        blank=True,
        null=True,
        default=None,
    )

    # Positive Commentary

    show_on_sustainable_banks_page = models.BooleanField(
        help_text="Positive. Check if bank should be shown on sustainable banks page.",
        default=False,
    )

    # DEPRECATED
    from_the_website = models.TextField(
        help_text="Deprecated. Text is not used in new SFI pages unless no other text is specified in prismic.",
        blank=True,
    )

    # DEPRECATED. Text has been moved to SFIPages in prismic
    our_take = models.TextField(
        help_text="Positive. used to to give our take on green banks", blank=True
    )

    institution_type = models.ManyToManyField(InstitutionType, blank=True, help_text="Positive")

    institution_credentials = models.ManyToManyField(
        InstitutionCredential, blank=True, help_text="Positive"
    )

    # General Commentary

    # DEPRECATED. Text has been moved to BankPage in prismic
    subtitle = models.TextField(
        help_text="This text has been or is in the process of being migrated to prismic and is now read only.",
        blank=True,
    )

    # DEPRECATED. Text has been moved to BankPage in prismic
    header = models.TextField(
        help_text="This text has been or is in the process of being migrated to prismic and is now read only.",
        blank=True,
    )

    # DEPRECATED. Text has been moved to BankPage in prismic
    summary = models.TextField(
        help_text="This text has been or is in the process of being migrated to prismic and is now read only.",
        blank=True,
    )

    # DEPRECATED. Text has been moved to BankPage in prismic
    details = models.TextField(
        help_text="This text has been or is in the process of being migrated to prismic and is now read only.",
        blank=True,
    )

    def __repr__(self):
        return f"Commentary: {self.brand.tag}"

    def __str__(self):
        return f"Commentary: {self.brand.tag}"

    def clean(self):
        # Ensure no cycles when saving
        self.compute_inherited_rating(throw_error=True)

    def save(self, *args, **kwargs):
        if self.inherit_brand_rating:
            self.rating = RatingChoice.INHERIT

        if self.fossil_free_alliance and self.fossil_free_alliance_rating < 0:
            self.fossil_free_alliance_rating = 0
        elif not self.fossil_free_alliance:
            self.fossil_free_alliance_rating = -1

        return super().save(*args, **kwargs)
