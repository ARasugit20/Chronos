from app.models.model_run import ModelRun
from app.pipeline.features import FEATURE_NAMES, feature_schema_hash


def test_feature_schema_hash_is_stable_and_complete() -> None:
    assert len(FEATURE_NAMES) == 7
    assert len(feature_schema_hash()) == 64
    assert feature_schema_hash() == feature_schema_hash()


def test_model_run_tracks_reproducibility_fields() -> None:
    columns = ModelRun.__table__.columns
    for field in (
        "dataset_cutoff_at",
        "feature_schema_hash",
        "artifact_path",
        "parameters_json",
        "oos_brier",
        "oos_hit_rate",
    ):
        assert field in columns
