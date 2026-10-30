from __future__ import annotations

from app.cleaning.actions.convert_disguised import ConvertDisguisedMissing
from app.cleaning.actions.fill_missing import FillMissing
from app.cleaning.actions.fix_invalid_numeric import FixInvalidNumeric
from app.cleaning.actions.fix_rule import FixOutOfRange, FixRuleViolation
from app.cleaning.actions.handle_outliers import HandleOutliers
from app.cleaning.actions.merge_similar import MergeSimilarValues
from app.cleaning.actions.normalize_booleans import NormalizeBooleans
from app.cleaning.actions.normalize_case import NormalizeCaseVariants
from app.cleaning.actions.normalize_numbers import NormalizeNumbers
from app.cleaning.actions.remove_dups import RemoveDuplicateRows
from app.cleaning.actions.resolve_dup_ids import ResolveDuplicateIds
from app.cleaning.actions.standardize_dates import StandardizeDates
from app.cleaning.actions.trim_whitespace import TrimWhitespace

ACTIONS = [
    TrimWhitespace(),
    ConvertDisguisedMissing(),
    NormalizeCaseVariants(),
    NormalizeNumbers(),
    NormalizeBooleans(),
    StandardizeDates(),
    RemoveDuplicateRows(),
    FixInvalidNumeric(),
    FillMissing(),
    MergeSimilarValues(),
    FixOutOfRange(),
    FixRuleViolation(),
    HandleOutliers(),
    ResolveDuplicateIds(),
]
BY_ID = {a.id: a for a in ACTIONS}


def for_issue(issue):
    return [a for a in ACTIONS if a.applies(issue)]
