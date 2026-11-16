"""The application stage files whose construction has a recorded refusal."""

REFUSED_STAGE_FILES = {
    # the two entrepreneur stages list a control beside the label of their
    # branches; the four housing files define a set by a grid constructor or
    # select a family by a discrete state
    "cagetti-denardi-2006/declaration/stages/old_entrepreneur/old_entrepreneur.bl": (
        "not-constructed",
        "beside its branches",
    ),
    "cagetti-denardi-2006/declaration/stages/young_entrepreneur/young_entrepreneur.bl": (
        "not-constructed",
        "beside its branches",
    ),
    "housing-owner/declaration/stages/consumption_choice/consumption_choice.bl": (
        "not-constructed",
        "grid constructor",
    ),
    "housing-owner/declaration/stages/housing_choice/housing_choice.bl": (
        "family-selection",
        "z_vals[y]",
    ),
    "housing-renting/declaration/stages/owner_housing/owner_housing.bl": (
        "not-constructed",
        "grid constructor",
    ),
    "housing-renting/declaration/stages/renter_housing/renter_housing.bl": (
        "not-constructed",
        "grid constructor",
    ),
}
